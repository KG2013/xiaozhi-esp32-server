package smhs.modules.agent.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 智能体 - 角色的欢迎语和离场结束语
 * @author wmyuan
 */
@Data
@Schema(description = "智能体 - 角色的欢迎语和离场结束语对象")
public class GreetingLeaveMessageVO {

    @Schema(description = "开场欢迎语")
    private String greetingMessage;

    @Schema(description = "立场结束语")
    private String leaveMessage;
}
