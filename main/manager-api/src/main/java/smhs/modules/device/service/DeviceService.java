package smhs.modules.device.service;

import java.util.Date;
import java.util.List;

import smhs.common.page.PageData;
import smhs.common.service.BaseService;
import smhs.modules.device.dto.*;
import smhs.modules.device.entity.DeviceEntity;
import smhs.modules.device.vo.DeviceDetailVO;
import smhs.modules.device.vo.GenerateCodeVO;
import smhs.modules.device.vo.PageDeviceVO;
import smhs.modules.device.vo.UserShowDeviceListVO;
import smhs.modules.sys.dto.AdminPageUserDTO;
import smhs.modules.sys.vo.AdminPageUserVO;

public interface DeviceService extends BaseService<DeviceEntity> {

    /**
     * 检查设备是否激活
     */
    DeviceReportRespDTO checkDeviceActive(DeviceReportReqDTO deviceReport);

    /**
     * 获取用户指定智能体的设备列表，
     */
    List<DeviceEntity> getUserDevices(Long userId, String agentId);

    /**
     * 解绑设备
     */
    void unbindDevice(Long userId, String deviceId);

    /**
     * 设备激活
     */
    Boolean deviceActivation(String agentId, String activationCode);

    /**
     * 删除此用户的所有设备
     *
     * @param userId 用户id
     */
    void deleteByUserId(Long userId);

    /**
     * 删除指定智能体关联的所有设备
     *
     * @param agentId 智能体id
     */
    void deleteByAgentId(String agentId);

    /**
     * 获取指定用户的设备数量
     *
     * @param userId 用户id
     * @return 设备数量
     */
    Long selectCountByUserId(Long userId);

    /**
     * 分页获取全部设备信息
     *
     * @param dto 分页查找参数
     * @return 用户列表分页数据
     */
    PageData<UserShowDeviceListVO> page(DevicePageUserDTO dto);

    /**
     * 根据MAC地址获取设备信息
     *
     * @param macAddress MAC地址
     * @return 设备信息
     */
    DeviceEntity getDeviceByMacAddress(String macAddress);

    /**
     * 根据设备编码地址获取设备信息
     *
     * @param ssid 设备编码
     * @return 设备信息
     */
    DeviceEntity getDeviceBySsid(String ssid);

    /**
     * 根据设备ID获取激活码
     *
     * @param deviceId 设备ID
     * @return 激活码
     */
    String geCodeByDeviceId(String deviceId);

    /**
     * 根据设备ID获取激活码
     *
     * @param ssid 设备ID
     * @return 激活码
     */
    String geCodeBySsid(String ssid);

    /**
     * 获取这个智能体设备理的最近的最后连接时间
     *
     * @param agentId 智能体id
     * @return 返回设备最近的最后连接时间
     */
    Date getLatestLastConnectionTime(String agentId);

    /**
     * 手动添加设备
     */
    void manualAddDevice(Long userId, DeviceManualAddDTO dto);

    /**
     * 更新设备连接信息
     */
    void updateDeviceConnectionInfo(String agentId, String deviceId, String appVersion);

    /**
     * 添加绑定设备
     *
     * @param deviceAddBindDTO 添加绑定设备参数
     */
    void addBindDevice(DeviceAddBindDTO deviceAddBindDTO);

    /**
     * 删除设备
     *
     * @param ssid 设备编码
     */
    void deleteDevice(String ssid);

    /**
     * 设备状态改变
     *
     * @param ssid         设备编码
     * @param deviceStatus 设备状态
     */
    void deviceStatusChange(String ssid, boolean deviceStatus);


    /**
     * 设备管理带参分页
     *
     * @param dto 分页查找参数
     * @return 设备列表分页数据
     */
    PageData<PageDeviceVO> page(PageDeviceDTO dto);

    /**
     * 生成设备码
     *
     * @param codeVO 用户生成设备编码的传入参数实体对象
     * @return 生成好的设备码
     */
    String generateDeviceCode(GenerateCodeVO codeVO);

    /**
     * 批量生成设备码
     *
     * @param codeVO 用户生成设备编码的传入参数实体对象
     * @return 生成好的设备码
     */
    List<String> batchGenerateDeviceCode(GenerateCodeVO codeVO);

    /**
     * 设备详情信息
     *
     * @param ssid 设备编码
     * @return 设备详情信息
     */
    DeviceDetailVO deviceDetailInfo(String ssid);

    /**
     * 绑定设备蓝牙Id根据设备编码
     *
     * @param bluetoothIdDTO 绑定蓝牙id参数
     */
    void bindBluetoothIdBySsid(DeviceBindBluetoothIdDTO bluetoothIdDTO);
}