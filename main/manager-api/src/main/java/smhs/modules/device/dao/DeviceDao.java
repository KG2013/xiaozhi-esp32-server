package smhs.modules.device.dao;

import java.util.Date;
import java.util.List;
import java.util.Map;

import org.apache.ibatis.annotations.Mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import org.apache.ibatis.annotations.Param;
import smhs.modules.device.dto.DeviceBindBluetoothIdDTO;
import smhs.modules.device.entity.DeviceEntity;
import smhs.modules.device.vo.PageDeviceVO;

@Mapper
public interface DeviceDao extends BaseMapper<DeviceEntity> {
    /**
     * 获取此智能体全部设备的最后连接时间
     *
     * @param agentId 智能体id
     * @return
     */
    Date getAllLastConnectedAtByAgentId(String agentId);

    /**
     * 使用MyBatis-Plus查询数据库中最大的序列号
     *
     * @param deviceCodePrefix 设备编码前缀
     * @return 返回设备编码自增序号
     */
    Map<String, Object> selectMap(@Param("deviceCodePrefix") String deviceCodePrefix);

    /**
     * 绑定设备蓝牙Id根据设备编码
     *
     * @param bluetoothIdDTO 绑定蓝牙id参数
     */
    void bindBluetoothIdBySsid(DeviceBindBluetoothIdDTO bluetoothIdDTO);

    List<PageDeviceVO> selectDeviceBluetoothIdList(PageDeviceVO pageDeviceVO);
}