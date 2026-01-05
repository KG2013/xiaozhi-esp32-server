package smhs.modules.config.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.Map;

@Data
@Schema(description = "获取智能体模型配置DTO")
public class AgentModelsNewDTO {

    @NotBlank(message = "设备编码不能为空")
    @Schema(description = "设备编码")
    private String ssid;

    @NotBlank(message = "客户端ID不能为空")
    @Schema(description = "客户端ID")
    private String clientId;

    @NotNull(message = "客户端已实例化的模型不能为空")
    @Schema(description = "客户端已实例化的模型")
    private Map<String, String> selectedModule;
}