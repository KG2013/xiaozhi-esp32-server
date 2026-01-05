package smhs.modules.agent.dao;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import org.apache.ibatis.annotations.Select;
import smhs.common.dao.BaseDao;
import smhs.modules.agent.entity.AgentEntity;
import smhs.modules.agent.vo.AgentInfoVO;
import smhs.modules.agent.vo.GreetingLeaveMessageVO;

@Mapper
public interface AgentDao extends BaseDao<AgentEntity> {
    /**
     * 获取智能体的设备数量
     * 
     * @param agentId 智能体ID
     * @return 设备数量
     */
    Integer getDeviceCountByAgentId(@Param("agentId") String agentId);

    /**
     * 根据设备MAC地址查询对应设备的默认智能体信息
     *
     * @param macAddress 设备MAC地址
     * @return 默认智能体信息
     */
    @Select(" SELECT a.* FROM ai_device d " +
            " LEFT JOIN ai_agent a ON d.agent_id = a.id " +
            " WHERE d.mac_address = #{macAddress} " +
            " ORDER BY d.id DESC LIMIT 1")
    AgentEntity getDefaultAgentByMacAddress(@Param("macAddress") String macAddress);

    /**
     * 根据设备编码查询对应设备的默认智能体信息
     *
     * @param ssid 设备编码
     * @return 默认智能体信息
     */
    @Select(" SELECT a.* FROM ai_device d " +
            " LEFT JOIN ai_agent a ON d.agent_id = a.id " +
            " WHERE d.ssid = #{ssid} " +
            " ORDER BY d.id DESC LIMIT 1")
    AgentEntity getDefaultAgentBySsid(@Param("ssid") String ssid);

    /**
     * 根据id查询agent信息，包括插件信息
     *
     * @param agentId 智能体ID
     */
    AgentInfoVO selectAgentInfoById(@Param("agentId") String agentId);

    /**
     * 获取智能体（角色）开场欢迎语和离场结束语
     *
     * @param agentId 智能体Id
     * @return 角色的欢迎语和离场结束语 对象
     */
    GreetingLeaveMessageVO getGreetingAndLeave(@Param("agentId") String agentId);
}
