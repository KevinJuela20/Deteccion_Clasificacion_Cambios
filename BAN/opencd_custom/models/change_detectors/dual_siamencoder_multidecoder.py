from typing import List, Optional

import torch
import torch.nn.functional as F
from torch import Tensor

from mmseg.models.segmentors.base import BaseSegmentor
from mmseg.utils import (ConfigType, OptConfigType, OptMultiConfig,
                         OptSampleList, SampleList, add_prefix)

from opencd.registry import MODELS

from mmseg.models.utils import resize
from mmseg.structures import SegDataSample
from mmseg.utils import (ConfigType, OptConfigType, OptMultiConfig,
                         OptSampleList, SampleList, add_prefix)
from mmengine.structures import PixelData


@MODELS.register_module()
class DualSiamEncoderMultiDecoder(BaseSegmentor):
    """Dual Siamese-Encoder Multi-Decoder.

    Bi-Temporal Adapter Network (BAN) for Remote Sensing
    Image Change Detection.

    1. The ``loss`` method is used to calculate the loss of model,
    which includes two steps: (1) Extracts features to obtain the feature maps
    (2) Call the decode head loss function to forward decode head model and
    calculate losses.

    .. code:: text

     loss(): extract_feat() -> _decode_head_forward_train()
     _decode_head_forward_train(): decode_head.loss()

    2. The ``predict`` method is used to predict segmentation results,
    which includes two steps: (1) Run inference function to obtain the list of
    seg_logits (2) Call post-processing function to obtain list of
    ``SegDataSampel`` including ``pred_sem_seg`` and ``seg_logits``.

    .. code:: text

     predict(): inference() -> postprocess_result()
     inference(): whole_inference()/slide_inference()
     whole_inference()/slide_inference(): encoder_decoder()
     encoder_decoder(): extract_feat() -> decode_head.predict()

    3. The ``_forward`` method is used to output the tensor by running the model,
    which includes two steps: (1) Extracts features to obtain the feature maps
    (2)Call the decode head forward function to forward decode head model.

    .. code:: text

     _forward(): extract_feat() -> _decode_head.forward()

    Args:

        image_encoder (ConfigType): The config for the visual encoder of segmentor.
        decode_head (ConfigType): The config for the decode head of segmentor.
        train_cfg (OptConfigType): The config for training. Defaults to None.
        test_cfg (OptConfigType): The config for testing. Defaults to None.
        data_preprocessor (dict, optional): The pre-process config of
            :class:`BaseDataPreprocessor`.
        pretrained (str, optional): The path for pretrained model.
            Defaults to None.
        asymetric_input (bool): whether to use different size of input for image encoder
            and decode head. Defaults to False.
        encoder_resolution (float): resize scale of input images for image encoder.
            Defaults to None.
        init_cfg (dict, optional): The weight initialized config for
            :class:`BaseModule`.
    """  # noqa: E501

    def __init__(self,
                 image_encoder: ConfigType,
                 decode_head: ConfigType,
                 postprocess_pred_and_label: Optional[str] = None, 
                 train_cfg: OptConfigType = None,
                 test_cfg: OptConfigType = None,
                 data_preprocessor: OptConfigType = None,
                 pretrained: Optional[str] = None,
                 asymetric_input: bool = True,
                 encoder_resolution: OptConfigType = None,
                 init_cfg: OptMultiConfig = None):
        super().__init__(
            data_preprocessor=data_preprocessor, init_cfg=init_cfg)
        if pretrained is not None:
            image_encoder.init_cfg = dict(
                type='Pretrained_Part', checkpoint=pretrained)
            decode_head.init_cfg = dict(
                type='Pretrained_Part', checkpoint=pretrained)

        if asymetric_input:
            assert encoder_resolution is not None, \
                'if asymetric_input set True, ' \
                'clip_resolution must be a certain value'
        self.asymetric_input = asymetric_input
        self.encoder_resolution = encoder_resolution
        self.image_encoder = MODELS.build(image_encoder)
        self._init_decode_head(decode_head)

        self.train_cfg = train_cfg
        self.test_cfg = test_cfg

        assert self.with_decode_head

        self.postprocess_pred_and_label = postprocess_pred_and_label

    def _init_decode_head(self, decode_head: ConfigType) -> None:
        """Initialize ``decode_head``"""
        # for binary branches
        self.decode_head = MODELS.build(decode_head)
        self.num_classes = self.decode_head.binary_cd_head.num_classes
        self.out_channels = self.decode_head.binary_cd_head.out_channels
        # for sementic branches
        self.semantic_num_classes = self.decode_head.semantic_cd_head.num_classes
        self.semantic_out_channels = self.decode_head.semantic_cd_head.out_channels

        self.align_corners = {
            'seg_logits': self.decode_head.binary_cd_head.align_corners,
            'seg_logits_from': self.decode_head.semantic_cd_head.align_corners,
            'seg_logits_to': self.decode_head.semantic_cd_head.align_corners}
        self.thresholds = {
            'seg_logits': self.decode_head.binary_cd_head.threshold,
            'seg_logits_from': self.decode_head.semantic_cd_head.threshold,
            'seg_logits_to': self.decode_head.semantic_cd_head.threshold}

    def extract_feat(self, inputs: Tensor) -> List[Tensor]:
        """Extract visual features from images."""
        x = self.image_encoder(inputs)
        return x

    def encode_decode(self, inputs: Tensor,
                      batch_img_metas: List[dict]) -> Tensor:
        """Encode the name of classes with text_encoder and encode images with
        image_encoder.

        Then decode the class embedding and visual feature into a semantic
        segmentation map of the same size as input.
        """
        img_from, img_to = torch.split(inputs, 3, dim=1)

        fm_img_from, fm_img_to = img_from, img_to
        if self.asymetric_input:
            fm_img_from = F.interpolate(
                fm_img_from, **self.encoder_resolution)
            fm_img_to = F.interpolate(
                fm_img_to, **self.encoder_resolution)
        fm_feat_from = self.image_encoder(fm_img_from)
        fm_feat_to = self.image_encoder(fm_img_to)
        seg_logits = self.decode_head.predict([img_from, img_to, fm_feat_from, fm_feat_to],
                                              batch_img_metas, self.test_cfg)

        return seg_logits

    def _decode_head_forward_train(self, inputs: List[Tensor],
                                   data_samples: SampleList) -> dict:
        """Run forward function and calculate loss for decode head in
        training."""
        losses = dict()
        loss_decode = self.decode_head.loss(inputs, data_samples,
                                            self.train_cfg)

        losses.update(add_prefix(loss_decode, 'decode'))
        return losses

    def loss(self, inputs: Tensor, data_samples: SampleList) -> dict:
        """Calculate losses from a batch of inputs and data samples.

        Args:
            inputs (Tensor): Input images.
            data_samples (list[:obj:`SegDataSample`]): The seg data samples.
                It usually includes information such as `metainfo` and
                `gt_sem_seg`.

        Returns:
            dict[str, Tensor]: a dictionary of loss components
        """
        img_from, img_to = torch.split(inputs, 3, dim=1)

        fm_img_from, fm_img_to = img_from, img_to
        if self.asymetric_input:
            fm_img_from = F.interpolate(
                fm_img_from, **self.encoder_resolution)
            fm_img_to = F.interpolate(
                fm_img_to, **self.encoder_resolution)
        fm_feat_from = self.image_encoder(fm_img_from)
        fm_feat_to = self.image_encoder(fm_img_to)

        losses = dict()

        loss_decode = self._decode_head_forward_train(
            [img_from, img_to, fm_feat_from, fm_feat_to], data_samples)
        losses.update(loss_decode)

        return losses

    def predict(self,
                inputs: Tensor,
                data_samples: OptSampleList = None) -> SampleList:
        """Predict results from a batch of inputs and data samples with post-
        processing.

        Args:
            inputs (Tensor): Inputs with shape (N, C, H, W).
            data_samples (List[:obj:`SegDataSample`], optional): The seg data
                samples. It usually includes information such as `metainfo`
                and `gt_sem_seg`.

        Returns:
            list[:obj:`SegDataSample`]: Segmentation results of the
            input images. Each SegDataSample usually contain:

            - ``pred_sem_seg``(PixelData): Prediction of semantic segmentation.
            - ``seg_logits``(PixelData): Predicted logits of semantic
                segmentation before normalization.
        """
        if data_samples is not None:
            batch_img_metas = [
                data_sample.metainfo for data_sample in data_samples
            ]
        else:
            batch_img_metas = [
                dict(
                    ori_shape=inputs.shape[2:],
                    img_shape=inputs.shape[2:],
                    pad_shape=inputs.shape[2:],
                    padding_size=[0, 0, 0, 0])
            ] * inputs.shape[0]

        seg_logits = self.inference(inputs, batch_img_metas)

        return self.postprocess_result(seg_logits, data_samples)

    def _forward(self,
                 inputs: Tensor,
                 data_samples: OptSampleList = None) -> Tensor:
        """Network forward process.

        Args:
            inputs (Tensor): Inputs with shape (N, C, H, W).
            data_samples (List[:obj:`SegDataSample`]): The seg
                data samples. It usually includes information such
                as `metainfo` and `gt_sem_seg`.

        Returns:
            Tensor: Forward output of model without any post-processes.
        """
        img_from, img_to = torch.split(inputs, 3, dim=1)

        fm_img_from, fm_img_to = img_from, img_to
        if self.asymetric_input:
            fm_img_from = F.interpolate(
                fm_img_from, **self.encoder_resolution)
            fm_img_to = F.interpolate(
                fm_img_to, **self.encoder_resolution)
        fm_feat_from = self.extract_feat(fm_img_from)
        fm_feat_to = self.extract_feat(fm_img_to)
        return self.decode_head.forward([img_from, img_to, fm_feat_from, fm_feat_to])

    def postprocess_result(self,
                           seg_logits: Tensor,
                           data_samples: OptSampleList = None) -> SampleList:
        """ Convert results list to `SegDataSample`.
        Args:
            seg_logits (Tensor): The segmentation results, seg_logits from
                model of each input image.
            data_samples (list[:obj:`SegDataSample`]): The seg data samples.
                It usually includes information such as `metainfo` and
                `gt_sem_seg`. Default to None.
        Returns:
            list[:obj:`SegDataSample`]: Segmentation results of the
            input images. Each SegDataSample usually contain:

            - ``pred_sem_seg``(PixelData): Prediction of semantic segmentation.
            - ``seg_logits``(PixelData): Predicted logits of semantic
                segmentation before normalization.
        """

        C = dict()
        for seg_name, seg_logit in seg_logits.items():
            batch_size, _C, H, W = seg_logit.shape
            C[seg_name] = _C

        if data_samples is None:
            data_samples = [SegDataSample() for _ in range(batch_size)]
            only_prediction = True
        else:
            only_prediction = False

        for i in range(batch_size):
            for seg_name, seg_logit in seg_logits.items():
                if not only_prediction:
                    img_meta = data_samples[i].metainfo
                    # remove padding area
                    if 'img_padding_size' not in img_meta:
                        padding_size = img_meta.get('padding_size', [0] * 4)
                    else:
                        padding_size = img_meta['img_padding_size']
                    padding_left, padding_right, padding_top, padding_bottom =\
                        padding_size
                    # i_seg_logit shape is 1, C, H, W after remove padding
                    i_seg_logit = seg_logit[i:i + 1, :,
                                            padding_top:H - padding_bottom,
                                            padding_left:W - padding_right]

                    flip = img_meta.get('flip', None)
                    if flip:
                        flip_direction = img_meta.get('flip_direction', None)
                        assert flip_direction in ['horizontal', 'vertical']
                        if flip_direction == 'horizontal':
                            i_seg_logit = i_seg_logit.flip(dims=(3, ))
                        else:
                            i_seg_logit = i_seg_logit.flip(dims=(2, ))

                    # resize as original shape
                    i_seg_logit = resize(
                        i_seg_logit,
                        size=img_meta['ori_shape'],
                        mode='bilinear',
                        align_corners=self.align_corners[seg_name],
                        warning=False).squeeze(0)
                else:
                    i_seg_logit = seg_logit[i]

                if C[seg_name] > 1:
                    i_seg_pred = i_seg_logit.argmax(dim=0, keepdim=True)
                else:
                    i_seg_logit = i_seg_logit.sigmoid()
                    i_seg_pred = (i_seg_logit >
                                    self.thresholds[seg_name]).to(i_seg_logit)
                
                pred_name = '_' + seg_name.split('_')[-1] \
                    if seg_name.split('_')[-1] in ['from', 'to'] else ''
                pred_name = 'pred_sem_seg' + pred_name
                data_samples[i].set_data({
                    seg_name:
                    PixelData(**{'data': i_seg_logit}),
                    pred_name:
                    PixelData(**{'data': i_seg_pred})
                })

        if self.postprocess_pred_and_label is not None:
            if self.postprocess_pred_and_label == 'cover_semantic':
                for data_sample in data_samples:
                    # postprocess_semantic_pred
                    data_sample.pred_sem_seg_from.data = data_sample.pred_sem_seg_from.data + 1
                    data_sample.pred_sem_seg_to.data = data_sample.pred_sem_seg_to.data + 1
                    data_sample.pred_sem_seg_from.data = data_sample.pred_sem_seg_from.data * \
                                                            data_sample.pred_sem_seg.data
                    data_sample.pred_sem_seg_to.data = data_sample.pred_sem_seg_to.data * \
                                                            data_sample.pred_sem_seg.data
                    
                    # postprocess_semantic_label
                    data_sample.gt_sem_seg_from.data[data_sample.gt_sem_seg_from.data == 255] = -1
                    data_sample.gt_sem_seg_from.data = data_sample.gt_sem_seg_from.data + 1
                    data_sample.gt_sem_seg_to.data[data_sample.gt_sem_seg_to.data == 255] = -1
                    data_sample.gt_sem_seg_to.data = data_sample.gt_sem_seg_to.data + 1
            else:
                raise ValueError(
                        f'`postprocess_pred_and_label` should be `cover_semantic` or None.')

        return data_samples

    def slide_inference(self, inputs: Tensor,
                        batch_img_metas: List[dict]) -> Tensor:
        """Inference by sliding-window with overlap.

        If h_crop > h_img or w_crop > w_img, the small patch will be used to
        decode without padding.

        Args:
            inputs (tensor): the tensor should have a shape NxCxHxW,
                which contains all images in the batch.
            batch_img_metas (List[dict]): List of image metainfo where each may
                also contain: 'img_shape', 'scale_factor', 'flip', 'img_path',
                'ori_shape', and 'pad_shape'.
                For details on the values of these keys see
                `mmseg/datasets/pipelines/formatting.py:PackSegInputs`.

        Returns:
            Tensor: The segmentation results, seg_logits from model of each
                input image.
        """

        h_stride, w_stride = self.test_cfg.stride
        h_crop, w_crop = self.test_cfg.crop_size
        batch_size, _, h_img, w_img = inputs.size()
        out_channels = self.out_channels
        semantic_channels = self.semantic_out_channels
        h_grids = max(h_img - h_crop + h_stride - 1, 0) // h_stride + 1
        w_grids = max(w_img - w_crop + w_stride - 1, 0) // w_stride + 1
        preds = dict(
            seg_logits=inputs.new_zeros((batch_size, out_channels, h_img, w_img)),
            seg_logits_from=inputs.new_zeros((batch_size, semantic_channels, h_img, w_img)), 
            seg_logits_to=inputs.new_zeros((batch_size, semantic_channels, h_img, w_img))
        )
        count_mat = inputs.new_zeros((batch_size, 1, h_img, w_img))
        for h_idx in range(h_grids):
            for w_idx in range(w_grids):
                y1 = h_idx * h_stride
                x1 = w_idx * w_stride
                y2 = min(y1 + h_crop, h_img)
                x2 = min(x1 + w_crop, w_img)
                y1 = max(y2 - h_crop, 0)
                x1 = max(x2 - w_crop, 0)
                crop_img = inputs[:, :, y1:y2, x1:x2]
                # change the image shape to patch shape
                batch_img_metas[0]['img_shape'] = crop_img.shape[2:]
                # the output of encode_decode is seg logits tensor map
                # with shape [N, C, H, W]
                crop_seg_logits = self.encode_decode(crop_img, batch_img_metas)
                for seg_name, crop_seg_logit in crop_seg_logits.items():
                    preds[seg_name] += F.pad(crop_seg_logit,
                                (int(x1), int(preds[seg_name].shape[3] - x2), int(y1),
                                    int(preds[seg_name].shape[2] - y2)))
                count_mat[:, :, y1:y2, x1:x2] += 1
        assert (count_mat == 0).sum() == 0
        for seg_name, pred in preds.items():
            preds[seg_name] = pred / count_mat

        return preds

    def whole_inference(self, inputs: Tensor,
                        batch_img_metas: List[dict]) -> Tensor:
        """Inference with full image.

        Args:
            inputs (Tensor): The tensor should have a shape NxCxHxW, which
                contains all images in the batch.
            batch_img_metas (List[dict]): List of image metainfo where each may
                also contain: 'img_shape', 'scale_factor', 'flip', 'img_path',
                'ori_shape', and 'pad_shape'.
                For details on the values of these keys see
                `mmseg/datasets/pipelines/formatting.py:PackSegInputs`.

        Returns:
            Tensor: The segmentation results, seg_logits from model of each
                input image.
        """

        seg_logits = self.encode_decode(inputs, batch_img_metas)

        return seg_logits

    def inference(self, inputs: Tensor, batch_img_metas: List[dict]) -> Tensor:
        """Inference with slide/whole style.

        Args:
            inputs (Tensor): The input image of shape (N, 3, H, W).
            batch_img_metas (List[dict]): List of image metainfo where each may
                also contain: 'img_shape', 'scale_factor', 'flip', 'img_path',
                'ori_shape', 'pad_shape', and 'padding_size'.
                For details on the values of these keys see
                `mmseg/datasets/pipelines/formatting.py:PackSegInputs`.

        Returns:
            Tensor: The segmentation results, seg_logits from model of each
                input image.
        """

        assert self.test_cfg.mode in ['slide', 'whole']
        ori_shape = batch_img_metas[0]['ori_shape']
        assert all(_['ori_shape'] == ori_shape for _ in batch_img_metas)
        if self.test_cfg.mode == 'slide':
            seg_logit = self.slide_inference(inputs, batch_img_metas)
        else:
            seg_logit = self.whole_inference(inputs, batch_img_metas)

        return seg_logit

    def aug_test(self, inputs, batch_img_metas, rescale=True):
        """Test with augmentations.

        Only rescale=True is supported.
        """
        # aug_test rescale all imgs back to ori_shape for now
        assert rescale
        # to save memory, we get augmented seg logit inplace
        seg_logit = self.inference(inputs[0], batch_img_metas[0], rescale)
        for i in range(1, len(inputs)):
            cur_seg_logit = self.inference(inputs[i], batch_img_metas[i],
                                           rescale)
            seg_logit += cur_seg_logit
        seg_logit /= len(inputs)
        seg_pred = seg_logit.argmax(dim=1)
        # unravel batch dim
        seg_pred = list(seg_pred)
        return seg_pred
