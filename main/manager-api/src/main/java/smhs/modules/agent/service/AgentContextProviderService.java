package smhs.modules.agent.service;

import smhs.common.service.BaseService;
import smhs.modules.agent.entity.AgentContextProviderEntity;

public interface AgentContextProviderService extends BaseService<AgentContextProviderEntity> {
    /**
     * 根据智能体ID获取上下文源配置
     * @param agentId 智能体ID
     * @return 上下文源配置实体
     */
    AgentContextProviderEntity getByAgentId(String agentId);

    /**
     * 保存或更新上下文源配置
     * @param entity 实体
     */
    void saveOrUpdateByAgentId(AgentContextProviderEntity entity);

    /**
     * 根据智能体ID删除上下文源配置
     * @param agentId 智能体ID
     */
    void deleteByAgentId(String agentId);
}
