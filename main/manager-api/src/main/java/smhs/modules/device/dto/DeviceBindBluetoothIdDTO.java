package smhs.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;

/**
 * @Author LanLanCoder
 * @Description 仅供设备蓝牙绑定设备编码使用
 * @Date 2025/12/9 14:31
 * @Version V1.1.0
 * @Copyright (c)LanLanCoder, Inc. All rights reserved.
 */
public class DeviceBindBluetoothIdDTO {

    /**
     * 设备编码
     */
    @Schema(description = "设备编码")
    private String ssid;

    /**
     * 蓝牙编码
     */
    @Schema(description = "蓝牙编码")
    private String bluetoothId;
}
