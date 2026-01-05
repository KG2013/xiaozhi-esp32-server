package smhs.modules.agent.dao;

import org.apache.ibatis.annotations.Mapper;
import smhs.common.dao.BaseDao;
import smhs.modules.agent.entity.AgentContextProviderEntity;

@Mapper
public interface AgentContextProviderDao extends BaseDao<AgentContextProviderEntity> {
}
