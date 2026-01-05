package smhs.modules.device.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.*;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("ai_device")
@Schema(description = "设备信息")
public class DeviceEntity {

    @TableId(type = IdType.ASSIGN_UUID)
    @Schema(description = "ID")
    private String id;

    @Schema(description = "关联用户ID")
    private Long userId;

    @Schema(description = "MAC地址")
    private String macAddress;

    @Schema(description = "最后连接时间")
    private Date lastConnectedAt;

    @Schema(description = "自动更新开关(0关闭/1开启)")
    private Integer autoUpdate;

    @Schema(description = "设备硬件型号")
    private String board;

    @Schema(description = "设备别名")
    private String alias;

    @Schema(description = "智能体ID")
    private String agentId;

    @Schema(description = "固件版本号")
    private String appVersion;

    @Schema(description = "排序")
    private Integer sort;

    /**
     * 逻辑删除标记（0：显示；1：隐藏）
     */
    @Schema(description = "逻辑删除标记（0：显示；1：隐藏）")
    @TableLogic
    private String delFlag;

    @Schema(description = "更新者")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "更新时间")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "创建者")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "创建时间")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;

    @Schema(description = "硬件编码")
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
     * 设备渠道（字典项）
     */
    @Schema(description = "设备渠道（字典项）")
    private String deviceChannel;

    /**
     * 设备系列（字典项）
     */
    @Schema(description = "设备系列（字典项）")
    private String deviceSeries;

    /**
     * 设备类型（字典项）
     */
    @Schema(description = "设备类型（字典项）")
    private String deviceType;

    /**
     * 设备型号（字典项）
     */
    @Schema(description = "设备型号（字典项）")
    private String deviceModel;

    /**
     * 设备月份（字典项）
     */
    @Schema(description = "设备月份（字典项）")
    private String deviceMonth;

    /**
     * 设备年份（字典项）
     */
    @Schema(description = "设备年份（字典项）")
    private String deviceYear;

    /**
     * 设备编码后八位
     */
    @Schema(description = "设备编码后八位")
    private String deviceSerialNumber;

    /**
     * 设备状态
     */
    @Schema(description = "设备状态")
    private String deviceStatus;

    /**
     * 备注
     */
    @Schema(description = "备注")
    private String remark;

}