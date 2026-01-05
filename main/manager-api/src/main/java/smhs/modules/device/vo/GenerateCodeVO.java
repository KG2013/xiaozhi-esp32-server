package smhs.modules.device.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.ToString;

/**
 * @author wmyuan
 */
@Data
@ToString
public class GenerateCodeVO {

    /**
     * 智能体id
     */
    @Schema(description = "智能体id")
    private String agentId;

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
     * 设备状态
     */
    @Schema(description = "设备状态")
    private String deviceStatus;

    /**
     * 设备年份（字典项）
     */
    @Schema(description = "设年份（字典项）")
    private String deviceYear;

    /**
     * 设备月份（字典项）
     */
    @Schema(description = "设备月份（字典项）")
    private String deviceMonth;

    /**
     * 设备批量生成数
     */
    @Schema(description = "设备批量生成数")
    private Integer deviceBatchNum;
}
