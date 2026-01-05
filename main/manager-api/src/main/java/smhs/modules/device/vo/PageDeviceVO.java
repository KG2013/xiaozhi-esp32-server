package smhs.modules.device.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.Date;

/**
 * 设备分页查询VO
 *
 * @author wmyuan
 * @since 2025-11-26
 */
@Data
public class PageDeviceVO {

    /**
     * 所属用户id
     */
    @Schema(description = "所属用户id")
    private Long userId;

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

    /**
     * 设备品牌 （字典项）
     */
    @Schema(description = "设备品牌 （字典项）")
    private String deviceBrand;


    /**
     * 设备品牌 （字典项） - 名称
     */
    @Schema(description = "设备品牌 （字典项）名称")
    private String deviceBrandName;

    /**
     * 设备渠道（字典项）
     */
    @Schema(description = "设备渠道（字典项）")
    private String deviceChannel;

    /**
     * 设备渠道（字典项） - 名称
     */
    @Schema(description = "设备渠道（字典项）名称")
    private String deviceChannelName;

    /**
     * 设备系列（字典项）
     */
    @Schema(description = "设备系列（字典项）")
    private String deviceSeries;

    /**
     * 设备系列（字典项）- 名称
     */
    @Schema(description = "设备系列（字典项）名称")
    private String deviceSeriesName;

    /**
     * 设备类型（字典项）
     */
    @Schema(description = "设备类型（字典项）")
    private String deviceType;

    /**
     * 设备类型（字典项） - 名称
     */
    @Schema(description = "设备类型（字典项）名称")
    private String deviceTypeName;

    /**
     * 设备型号（字典项）
     */
    @Schema(description = "设备型号（字典项）")
    private String deviceModel;

    /**
     * 设备型号（字典项） - 名称
     */
    @Schema(description = "设备型号（字典项）名称")
    private String deviceModelName;

    /**
     * 设备状态
     */
    @Schema(description = "设备状态")
    private String deviceStatus;

    /**
     * 设备状态 - 名称
     */
    @Schema(description = "设备状态名称")
    private String deviceStatusName;

    /**
     * 备注
     */
    @Schema(description = "备注")
    private String remark;

    /**
     * 创建时间
     */
    @Schema(description = "创建时间")
    private Date createDate;

    /**
     * 更新时间
     */
    @Schema(description = "更新时间")
    private Date updateDate;

}
