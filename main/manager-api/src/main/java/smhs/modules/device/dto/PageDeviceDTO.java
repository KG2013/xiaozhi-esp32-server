package smhs.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import lombok.Data;

/**
 * 设备分页参数DTO
 *
 * @author wmyuan
 * @since 2025-11-26
 */
@Data
@Schema(description = "设备分页参数DTO")
public class PageDeviceDTO {

    @Schema(description = "页数")
    @Min(value = 0, message = "{sort.number}")
    private String page;

    @Schema(description = "显示列数")
    @Min(value = 0, message = "{sort.number}")
    private String limit;

    /**
     * 设备状态
     */
    @Schema(description = "设备状态")
    private String deviceStatus;

    /**
     * 智能体id或者角色id
     */
    @Schema(description = "智能体id或者角色id")
    private String agentId;
}
