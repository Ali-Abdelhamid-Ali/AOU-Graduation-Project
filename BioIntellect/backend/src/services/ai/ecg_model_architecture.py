from __future__ import annotations

import tensorflow as tf  # type: ignore[reportMissingTypeStubs]
from tensorflow.keras import Model  # type: ignore[reportMissingTypeStubs]
from tensorflow.keras import layers  # type: ignore[reportMissingTypeStubs]
from tensorflow.keras.layers import (  # type: ignore[reportMissingTypeStubs]
    Concatenate,
    Dense,
    Dropout,
    GlobalAveragePooling1D,
    Input,
)


def _inception_module(
    x,
    nb_filters: int = 32,
    kernel_sizes: tuple[int, int, int] = (10, 20, 40),
    bottleneck_size: int = 32,
    name: str = "inception",
):
    in_channels = x.shape[-1]

    if (
        bottleneck_size is not None
        and in_channels is not None
        and in_channels > bottleneck_size
    ):
        x_bottleneck = layers.Conv1D(
            bottleneck_size,
            kernel_size=1,
            padding="same",
            use_bias=False,
            name=f"{name}_bottleneck",
        )(x)
    else:
        x_bottleneck = x

    branches = []
    for kernel_size in kernel_sizes:
        branch = layers.Conv1D(
            nb_filters,
            kernel_size=kernel_size,
            padding="same",
            use_bias=False,
            name=f"{name}_conv_k{kernel_size}",
        )(x_bottleneck)
        branches.append(branch)

    maxpool_branch = layers.MaxPooling1D(
        pool_size=3,
        strides=1,
        padding="same",
        name=f"{name}_maxpool",
    )(x)
    maxpool_branch = layers.Conv1D(
        nb_filters,
        kernel_size=1,
        padding="same",
        use_bias=False,
        name=f"{name}_mp_conv",
    )(maxpool_branch)
    branches.append(maxpool_branch)

    out = layers.Concatenate(name=f"{name}_concat")(branches)
    out = layers.BatchNormalization(name=f"{name}_bn")(out)
    out = layers.ReLU(name=f"{name}_relu")(out)
    return out


def build_inceptiontime_backbone(
    input_shape: tuple[int, int] = (5000, 12),
    nb_filters: int = 32,
    depth: int = 6,
    kernel_sizes: tuple[int, int, int] = (10, 20, 40),
    bottleneck_size: int = 32,
    downsample_stride: int = 5,
) -> Model:
    inputs = layers.Input(shape=input_shape, name="ecg_input")

    if downsample_stride > 1:
        x = layers.Conv1D(
            nb_filters,
            kernel_size=downsample_stride * 2,
            strides=downsample_stride,
            padding="same",
            use_bias=False,
            name="initial_downsample",
        )(inputs)
        x = layers.BatchNormalization(name="initial_downsample_bn")(x)
        x = layers.ReLU(name="initial_downsample_relu")(x)
    else:
        x = inputs

    residual = x
    n_out_channels = nb_filters * (len(kernel_sizes) + 1)

    for i in range(depth):
        x = _inception_module(
            x,
            nb_filters=nb_filters,
            kernel_sizes=kernel_sizes,
            bottleneck_size=bottleneck_size,
            name=f"inception_{i}",
        )

        if (i + 1) % 3 == 0:
            shortcut = layers.Conv1D(
                n_out_channels,
                kernel_size=1,
                padding="same",
                use_bias=False,
                name=f"res_conv_{i}",
            )(residual)
            shortcut = layers.BatchNormalization(name=f"res_bn_{i}")(shortcut)

            x = layers.Add(name=f"res_add_{i}")([x, shortcut])
            x = layers.ReLU(name=f"res_relu_{i}")(x)
            residual = x

    x = GlobalAveragePooling1D(name="gap")(x)
    return Model(inputs=inputs, outputs=x, name="InceptionTime_Backbone")


def build_multimodal_head(
    backbone: Model,
    signal_shape: tuple[int, int],
    num_csv_features: int,
    num_classes: int,
    model_name: str = "Multimodal_ECG",
) -> Model:
    signal_input = Input(shape=signal_shape, dtype=tf.float32, name="signal_input")
    csv_input = Input(shape=(num_csv_features,), dtype=tf.float32, name="csv_input")

    signal_features = backbone(signal_input)

    csv_x = Dense(64, activation="relu", dtype="float32", name="csv_dense1")(csv_input)
    csv_x = Dropout(0.15, name="csv_dropout1")(csv_x)
    csv_x = Dense(32, activation="relu", dtype="float32", name="csv_dense2")(csv_x)

    merged = Concatenate(name="fusion")([signal_features, csv_x])

    x = Dense(256, activation="relu", dtype="float32", name="head_dense1")(merged)
    x = Dropout(0.30, name="head_dropout1")(x)
    x = Dense(128, activation="relu", dtype="float32", name="head_dense2")(x)
    x = Dropout(0.20, name="head_dropout2")(x)
    output = Dense(num_classes, activation="sigmoid", dtype="float32", name="output")(x)

    return Model(inputs=[signal_input, csv_input], outputs=output, name=model_name)


def build_multimodal_inceptiontime(
    signal_shape: tuple[int, int],
    num_csv_features: int,
    num_classes: int,
    nb_filters: int = 32,
    depth: int = 6,
    downsample_stride: int = 5,
) -> Model:
    backbone = build_inceptiontime_backbone(
        input_shape=signal_shape,
        nb_filters=nb_filters,
        depth=depth,
        downsample_stride=downsample_stride,
    )

    return build_multimodal_head(
        backbone=backbone,
        signal_shape=signal_shape,
        num_csv_features=num_csv_features,
        num_classes=num_classes,
        model_name="Multimodal_InceptionTime",
    )
