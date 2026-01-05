package smhs.modules.device.dto;

import com.baomidou.mybatisplus.annotation.TableField;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 新增设备绑定DTO
 *
 * @author wmyuan
 * @since 2025-11-26
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "设备连接头信息")
public class DeviceAddBindDTO {

    /**
     * 所属用户id
     */
    @Schema(description = "所属用户id")
    private Long userId;

    /**
     * 智能体id
     */
    @Schema(description = "智能体id")
    private String agentId;

    /**
     * 设备名称 集合
     */
    @TableField(exist = false)
    private String[] ssids;

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
     * 备注
     */
    @Schema(description = "备注")
    private String remark;
}
