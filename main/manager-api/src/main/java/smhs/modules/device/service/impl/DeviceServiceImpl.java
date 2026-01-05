package smhs.modules.device.service.impl;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import cn.hutool.core.util.ObjectUtil;
import org.apache.commons.lang3.StringUtils;
import org.springframework.aop.framework.AopContext;
import org.springframework.beans.BeanUtils;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;

import cn.hutool.core.util.RandomUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import smhs.common.constant.Constant;
import smhs.common.exception.ErrorCode;
import smhs.common.exception.RenException;
import smhs.common.page.PageData;
import smhs.common.redis.RedisKeys;
import smhs.common.redis.RedisUtils;
import smhs.common.service.impl.BaseServiceImpl;
import smhs.common.user.UserDetail;
import smhs.common.utils.ConvertUtils;
import smhs.common.utils.DateUtils;
import smhs.modules.device.dao.DeviceDao;
import smhs.modules.device.dto.*;
import smhs.modules.device.entity.DeviceEntity;
import smhs.modules.device.entity.OtaEntity;
import smhs.modules.device.service.DeviceService;
import smhs.modules.device.service.OtaService;
import smhs.modules.device.vo.DeviceDetailVO;
import smhs.modules.device.vo.GenerateCodeVO;
import smhs.modules.device.vo.PageDeviceVO;
import smhs.modules.device.vo.UserShowDeviceListVO;
import smhs.modules.security.user.SecurityUser;
import smhs.modules.sys.entity.SysUserEntity;
import smhs.modules.sys.service.SysDictDataService;
import smhs.modules.sys.service.SysParamsService;
import smhs.modules.sys.service.SysUserUtilService;
import smhs.modules.sys.vo.AdminPageUserVO;
import smhs.modules.sys.vo.SysDictDataItem;

@Slf4j
@Service
@AllArgsConstructor
public class DeviceServiceImpl extends BaseServiceImpl<DeviceDao, DeviceEntity> implements DeviceService {

    private final DeviceDao deviceDao;
    private final SysUserUtilService sysUserUtilService;
    private final SysParamsService sysParamsService;
    private final RedisUtils redisUtils;
    private final OtaService otaService;
    private final SysDictDataService dictDataService;

    @Async
    public void updateDeviceConnectionInfo(String agentId, String deviceId, String appVersion) {
        try {
            DeviceEntity device = new DeviceEntity();
            device.setId(deviceId);
            device.setLastConnectedAt(new Date());
            if (StringUtils.isNotBlank(appVersion)) {
                device.setAppVersion(appVersion);
            }
            deviceDao.updateById(device);
            if (StringUtils.isNotBlank(agentId)) {
                redisUtils.set(RedisKeys.getAgentDeviceLastConnectedAtById(agentId), new Date());
            }
        } catch (Exception e) {
            log.error("异步更新设备连接信息失败", e);
        }
    }

    @Override
    public Boolean deviceActivation(String agentId, String activationCode) {
        if (StringUtils.isBlank(activationCode)) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_EMPTY);
        }
        String deviceKey = "ota:activation:code:" + activationCode;
        Object cacheDeviceId = redisUtils.get(deviceKey);
        if (cacheDeviceId == null) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_ERROR);
        }
        String deviceId = (String) cacheDeviceId;
        String safeDeviceId = deviceId;
        String cacheDeviceKey = String.format("ota:activation:data:%s", safeDeviceId);
        Map<String, Object> cacheMap = (Map<String, Object>) redisUtils.get(cacheDeviceKey);
        if (cacheMap == null) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_ERROR);
        }
        String cachedCode = (String) cacheMap.get("activation_code");
        if (!activationCode.equals(cachedCode)) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_ERROR);
        }
        // 检查设备有没有被激活
        if (selectById(deviceId) != null) {
            throw new RenException(ErrorCode.DEVICE_ALREADY_ACTIVATED);
        }

        String macAddress = (String) cacheMap.get("mac_address");
        String board = (String) cacheMap.get("board");
        String appVersion = (String) cacheMap.get("app_version");
        UserDetail user = SecurityUser.getUser();
        if (user.getId() == null) {
            throw new RenException(ErrorCode.USER_NOT_LOGIN);
        }

        Date currentTime = new Date();
        DeviceEntity deviceEntity = new DeviceEntity();
        //deviceEntity.setId(deviceId);
        deviceEntity.setSsid(safeDeviceId);
        deviceEntity.setBoard(board);
        deviceEntity.setAgentId(agentId);
        deviceEntity.setAppVersion(appVersion);
        deviceEntity.setMacAddress(macAddress);
        deviceEntity.setUserId(user.getId());
        deviceEntity.setCreator(user.getId());
        deviceEntity.setAutoUpdate(1);
        deviceEntity.setCreateDate(currentTime);
        deviceEntity.setUpdater(user.getId());
        deviceEntity.setUpdateDate(currentTime);
        deviceEntity.setLastConnectedAt(currentTime);
        deviceDao.insert(deviceEntity);

        // 清理redis缓存
        redisUtils.delete(cacheDeviceKey);
        redisUtils.delete(deviceKey);

        // 添加：清除智能体设备数量缓存
        redisUtils.delete(RedisKeys.getAgentDeviceCountById(agentId));

        return true;
    }

    @Override
    public DeviceReportRespDTO checkDeviceActive(DeviceReportReqDTO deviceReport) {

        DeviceReportRespDTO response = new DeviceReportRespDTO();
        response.setServer_time(buildServerTime());

        // 设备未绑定，则返回当前上传的固件信息（不更新）以此兼容旧固件版本
//        if (deviceById == null) {
//            DeviceReportRespDTO.Firmware firmware = new DeviceReportRespDTO.Firmware();
//            firmware.setVersion(deviceReport.getApplication().getVersion());
//            firmware.setUrl(Constant.INVALID_FIRMWARE_URL);
//            response.setFirmware(firmware);
//        } else {
//            // 只有在设备已绑定且autoUpdate不为0的情况下才返回固件升级信息
//            if (deviceById.getAutoUpdate() != 0) {
//
//            }
//        }

        String type = deviceReport.getBoard() == null ? null : deviceReport.getBoard().getType();
        DeviceReportRespDTO.Firmware firmware = buildFirmwareInfo(type, deviceReport.getApplication() == null ? null : deviceReport.getApplication().getVersion());
        response.setFirmware(firmware);

        // 添加WebSocket配置
        // DeviceReportRespDTO.Websocket websocket = new DeviceReportRespDTO.Websocket();
        // 从系统参数获取WebSocket URL，如果未配置则使用默认值
//        String wsUrl = sysParamsService.getValue(Constant.SERVER_WEBSOCKET, true);
//        websocket.setToken("");
//        if (StringUtils.isBlank(wsUrl) || wsUrl.equals("null")) {
//            log.error("WebSocket地址未配置，请登录智控台，在参数管理找到【server.websocket】配置");
//            wsUrl = "ws://smhs.n.langeving.com/smhs/v1/";
//            websocket.setUrl(wsUrl);
//        } else {
//            String[] wsUrls = wsUrl.split("\\;");
//            if (wsUrls.length > 0) {
//                // 随机选择一个WebSocket URL
//                websocket.setUrl(wsUrls[RandomUtil.randomInt(0, wsUrls.length)]);
//            } else {
//                log.error("WebSocket地址未配置，请登录智控台，在参数管理找到【server.websocket】配置");
//                websocket.setUrl("ws://smhs.n.langeving.com/smhs/v1/");
//            }
//        }
//
//        response.setWebsocket(websocket);

        // 添加MQTT UDP配置
        // 从系统参数获取MQTT Gateway地址，仅在配置有效时使用
//        String mqttUdpConfig = sysParamsService.getValue(Constant.SERVER_MQTT_GATEWAY, false);
//        if (mqttUdpConfig != null && !mqttUdpConfig.equals("null") && !mqttUdpConfig.isEmpty()) {
//            try {
//                String groupId = deviceById != null && deviceById.getBoard() != null ? deviceById.getBoard()
//                        : "GID_default";
//                DeviceReportRespDTO.MQTT mqtt = buildMqttConfig(macAddress, groupId);
//                if (mqtt != null) {
//                    mqtt.setEndpoint(mqttUdpConfig);
//                    response.setMqtt(mqtt);
//                }
//            } catch (Exception e) {
//                log.error("生成MQTT配置失败: {}", e.getMessage());
//            }
//        }

//        if (deviceById != null) {
//            // 如果设备存在，则异步更新上次连接时间和版本信息
//            String appVersion = deviceReport.getApplication() != null ? deviceReport.getApplication().getVersion()
//                    : null;
//            // 通过Spring代理调用异步方法
//            ((DeviceServiceImpl) AopContext.currentProxy()).updateDeviceConnectionInfo(deviceById.getAgentId(),
//                    deviceById.getId(), appVersion);
//        } else {
//            // 如果设备不存在，则生成激活码
//            DeviceReportRespDTO.Activation code = buildActivation(macAddress, deviceReport);
//            response.setActivation(code);
//        }

        return response;
    }

    @Override
    public List<DeviceEntity> getUserDevices(Long userId, String agentId) {
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("agent_id", agentId);
        return baseDao.selectList(wrapper);
    }

    @Override
    public void unbindDevice(Long userId, String deviceId) {
        // 先查询设备信息，获取agentId
        DeviceEntity device = baseDao.selectById(deviceId);
        if (device == null) {
            return;
        }
        if (StringUtils.isNotBlank(device.getAgentId())) {
            // 清除智能体设备数量缓存
            redisUtils.delete(RedisKeys.getAgentDeviceCountById(device.getAgentId()));
        }

        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("id", deviceId);
        baseDao.delete(wrapper);
    }

    @Override
    public void deleteByUserId(Long userId) {
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        baseDao.delete(wrapper);
    }

    @Override
    public Long selectCountByUserId(Long userId) {
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        return baseDao.selectCount(wrapper);
    }

    @Override
    public void deleteByAgentId(String agentId) {
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("agent_id", agentId);
        baseDao.delete(wrapper);
    }

    @Override
    public PageData<UserShowDeviceListVO> page(DevicePageUserDTO dto) {
        Map<String, Object> params = new HashMap<String, Object>();
        params.put(Constant.PAGE, dto.getPage());
        params.put(Constant.LIMIT, dto.getLimit());
        IPage<DeviceEntity> page = baseDao.selectPage(
                getPage(params, "mac_address", true),
                // 定义查询条件
                new QueryWrapper<DeviceEntity>()
                        // 必须设备关键词查找
                        .like(StringUtils.isNotBlank(dto.getKeywords()), "alias", dto.getKeywords()));
        // 循环处理page获取回来的数据，返回需要的字段
        List<UserShowDeviceListVO> list = page.getRecords().stream().map(device -> {
            UserShowDeviceListVO vo = ConvertUtils.sourceToTarget(device, UserShowDeviceListVO.class);
            // 把最后修改的时间，改为简短描述的时间
            vo.setRecentChatTime(DateUtils.getShortTime(device.getUpdateDate()));
            sysUserUtilService.assignUsername(device.getUserId(),
                    vo::setBindUserName);
            vo.setDeviceType(device.getBoard());
            return vo;
        }).toList();
        // 计算页数
        return new PageData<>(list, page.getTotal());
    }

    @Override
    public DeviceEntity getDeviceByMacAddress(String macAddress) {
        if (StringUtils.isBlank(macAddress)) {
            return null;
        }
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("mac_address", macAddress);
        return baseDao.selectOne(wrapper);
    }

    /**
     * 根据设备编码地址获取设备信息
     *
     * @param ssid 设备编码
     * @return 设备信息
     */
    @Override
    public DeviceEntity getDeviceBySsid(String ssid) {
        if (StringUtils.isBlank(ssid)) {
            return null;
        }
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("ssid", ssid);
        return baseDao.selectOne(wrapper);
    }

    private DeviceReportRespDTO.ServerTime buildServerTime() {
        DeviceReportRespDTO.ServerTime serverTime = new DeviceReportRespDTO.ServerTime();
        TimeZone tz = TimeZone.getDefault();
        serverTime.setTimestamp(Instant.now().toEpochMilli());
        serverTime.setTimeZone(tz.getID());
        serverTime.setTimezone_offset(tz.getOffset(System.currentTimeMillis()) / (60 * 1000));
        return serverTime;
    }

    @Override
    public String geCodeByDeviceId(String deviceId) {
        String dataKey = getDeviceCacheKey(deviceId);

        Map<String, Object> cacheMap = (Map<String, Object>) redisUtils.get(dataKey);
        if (cacheMap != null && cacheMap.containsKey("activation_code")) {
            String cachedCode = (String) cacheMap.get("activation_code");
            return cachedCode;
        }
        return null;
    }

    @Override
    public String geCodeBySsid(String ssid) {
        String dataKey = getDeviceCacheKeySsid(ssid);

        Map<String, Object> cacheMap = (Map<String, Object>) redisUtils.get(dataKey);
        if (cacheMap != null && cacheMap.containsKey("activation_code")) {
            String cachedCode = (String) cacheMap.get("activation_code");
            return cachedCode;
        }
        return null;
    }

    @Override
    public Date getLatestLastConnectionTime(String agentId) {
        // 查询是否有缓存时间，有则返回
        Date cachedDate = (Date) redisUtils.get(RedisKeys.getAgentDeviceLastConnectedAtById(agentId));
        if (cachedDate != null) {
            return cachedDate;
        }
        Date maxDate = deviceDao.getAllLastConnectedAtByAgentId(agentId);
        if (maxDate != null) {
            redisUtils.set(RedisKeys.getAgentDeviceLastConnectedAtById(agentId), maxDate);
        }
        return maxDate;
    }

    private String getDeviceCacheKey(String deviceId) {
        String safeDeviceId = deviceId.replace(":", "_").toLowerCase();
        String dataKey = String.format("ota:activation:data:%s", safeDeviceId);
        return dataKey;
    }

    private String getDeviceCacheKeySsid(String ssid) {
        String safeDeviceId = ssid;
        String dataKey = String.format("ota:activation:data:%s", safeDeviceId);
        return dataKey;
    }

    public DeviceReportRespDTO.Activation buildActivation(String deviceId, DeviceReportReqDTO deviceReport) {
        DeviceReportRespDTO.Activation code = new DeviceReportRespDTO.Activation();

        String cachedCode = geCodeByDeviceId(deviceId);

        if (StringUtils.isNotBlank(cachedCode)) {
            code.setCode(cachedCode);
            String frontedUrl = sysParamsService.getValue(Constant.SERVER_FRONTED_URL, true);
            code.setMessage(frontedUrl + "\n" + cachedCode);
            code.setChallenge(deviceId);
        } else {
            String newCode = RandomUtil.randomNumbers(6);
            code.setCode(newCode);
            String frontedUrl = sysParamsService.getValue(Constant.SERVER_FRONTED_URL, true);
            code.setMessage(frontedUrl + "\n" + newCode);
            code.setChallenge(deviceId);

            Map<String, Object> dataMap = new HashMap<>();
            dataMap.put("id", deviceId);
            dataMap.put("mac_address", deviceId);

            dataMap.put("board", (deviceReport.getBoard() != null && deviceReport.getBoard().getType() != null)
                    ? deviceReport.getBoard().getType()
                    : (deviceReport.getChipModelName() != null ? deviceReport.getChipModelName() : "unknown"));
            dataMap.put("app_version", (deviceReport.getApplication() != null)
                    ? deviceReport.getApplication().getVersion()
                    : null);

            dataMap.put("deviceId", deviceId);
            dataMap.put("activation_code", newCode);

            // 写入主数据 key
            String dataKey = getDeviceCacheKey(deviceId);
            redisUtils.set(dataKey, dataMap);

            // 写入反查激活码 key
            String codeKey = "ota:activation:code:" + newCode;
            redisUtils.set(codeKey, deviceId);
        }
        return code;
    }

    private DeviceReportRespDTO.Firmware buildFirmwareInfo(String type, String currentVersion) {
        if (StringUtils.isBlank(type)) {
            return null;
        }
        if (StringUtils.isBlank(currentVersion)) {
            currentVersion = "0.0.0";
        }

        OtaEntity ota = otaService.getLatestOta(type);
        DeviceReportRespDTO.Firmware firmware = new DeviceReportRespDTO.Firmware();
        String downloadUrl = null;

        if (ota != null) {
            // 如果设备没有版本信息，或者OTA版本比设备版本新，则返回下载地址
            if (compareVersions(ota.getVersion(), currentVersion) > 0) {
                String otaUrl = sysParamsService.getValue(Constant.SERVER_OTA, true);
                if (StringUtils.isBlank(otaUrl) || otaUrl.equals("null")) {
                    log.error("OTA地址未配置，请登录智控台，在参数管理找到【server.ota】配置");
                    // 尝试从请求中获取
                    HttpServletRequest request = ((ServletRequestAttributes) RequestContextHolder
                            .getRequestAttributes())
                            .getRequest();
                    otaUrl = request.getRequestURL().toString();
                }
                // 将URL中的/ota/替换为/otaMag/download/
                String uuid = UUID.randomUUID().toString();
                redisUtils.set(RedisKeys.getOtaIdKey(uuid), ota.getId());
                downloadUrl = otaUrl.replace("/ota/", "/otaMag/download/") + uuid;
            }
        }

        firmware.setVersion(ota == null ? currentVersion : ota.getVersion());
        firmware.setUrl(downloadUrl == null ? Constant.INVALID_FIRMWARE_URL : downloadUrl);
        return firmware;
    }

    /**
     * 比较两个版本号
     *
     * @param version1 版本1
     * @param version2 版本2
     * @return 如果version1 > version2返回1，version1 < version2返回-1，相等返回0
     */
    private static int compareVersions(String version1, String version2) {
        if (version1 == null || version2 == null) {
            return 0;
        }

        String[] v1Parts = version1.split("\\.");
        String[] v2Parts = version2.split("\\.");

        int length = Math.max(v1Parts.length, v2Parts.length);
        for (int i = 0; i < length; i++) {
            int v1 = i < v1Parts.length ? Integer.parseInt(v1Parts[i]) : 0;
            int v2 = i < v2Parts.length ? Integer.parseInt(v2Parts[i]) : 0;

            if (v1 > v2) {
                return 1;
            } else if (v1 < v2) {
                return -1;
            }
        }
        return 0;
    }

    @Override
    public void manualAddDevice(Long userId, DeviceManualAddDTO dto) {
        // 检查mac是否已存在
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("mac_address", dto.getMacAddress());
        DeviceEntity exist = baseDao.selectOne(wrapper);
        if (exist != null) {
            throw new RenException(ErrorCode.MAC_ADDRESS_ALREADY_EXISTS);
        }
        Date now = new Date();
        DeviceEntity entity = new DeviceEntity();
        entity.setId(dto.getMacAddress());
        entity.setUserId(userId);
        entity.setAgentId(dto.getAgentId());
        entity.setBoard(dto.getBoard());
        entity.setAppVersion(dto.getAppVersion());
        entity.setMacAddress(dto.getMacAddress());
        entity.setCreateDate(now);
        entity.setUpdateDate(now);
        entity.setLastConnectedAt(now);
        entity.setCreator(userId);
        entity.setUpdater(userId);
        entity.setAutoUpdate(1);
        baseDao.insert(entity);

        // 添加：清除智能体设备数量缓存
        redisUtils.delete(RedisKeys.getAgentDeviceCountById(dto.getAgentId()));
    }

    /**
     * 生成MQTT密码签名
     *
     * @param content   签名内容 (clientId + '|' + username)
     * @param secretKey 密钥
     * @return Base64编码的HMAC-SHA256签名
     */
    private String generatePasswordSignature(String content, String secretKey) throws Exception {
        Mac hmac = Mac.getInstance("HmacSHA256");
        SecretKeySpec keySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
        hmac.init(keySpec);
        byte[] signature = hmac.doFinal(content.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(signature);
    }

    /**
     * 构建MQTT配置信息
     *
     * @param macAddress MAC地址
     * @param groupId    分组ID
     * @return MQTT配置对象
     */
    private DeviceReportRespDTO.MQTT buildMqttConfig(String macAddress, String groupId)
            throws Exception {
        // 从环境变量或系统参数获取签名密钥
        String signatureKey = sysParamsService.getValue("server.mqtt_signature_key", false);
        if (StringUtils.isBlank(signatureKey)) {
            log.warn("缺少MQTT_SIGNATURE_KEY，跳过MQTT配置生成");
            return null;
        }

        // 构建客户端ID格式：groupId@@@macAddress@@@uuid
        String groupIdSafeStr = groupId.replace(":", "_");
        String deviceIdSafeStr = macAddress.replace(":", "_");
        String mqttClientId = String.format("%s@@@%s@@@%s", groupIdSafeStr, deviceIdSafeStr, deviceIdSafeStr);

        // 构建用户数据（包含IP等信息）
        Map<String, String> userData = new HashMap<>();
        // 尝试获取客户端IP
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder
                    .getRequestAttributes();
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();
                String clientIp = request.getRemoteAddr();
                userData.put("ip", clientIp);
            }
        } catch (Exception e) {
            userData.put("ip", "unknown");
        }

        // 将用户数据编码为Base64 JSON
        String userDataJson = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(userData);
        String username = Base64.getEncoder().encodeToString(userDataJson.getBytes(StandardCharsets.UTF_8));

        // 生成密码签名
        String password = generatePasswordSignature(mqttClientId + "|" + username, signatureKey);

        // 构建MQTT配置
        DeviceReportRespDTO.MQTT mqtt = new DeviceReportRespDTO.MQTT();
        mqtt.setClient_id(mqttClientId);
        mqtt.setUsername(username);
        mqtt.setPassword(password);
        mqtt.setPublish_topic("device-server");
        mqtt.setSubscribe_topic("devices/p2p/" + deviceIdSafeStr);

        return mqtt;
    }

    /**
     * 添加绑定设备
     *
     * @param deviceAddBindDTO 添加绑定设备参数
     */
    @Override
    public void addBindDevice(DeviceAddBindDTO deviceAddBindDTO) {
        if (deviceAddBindDTO.getSsids() == null || deviceAddBindDTO.getSsids().length == 0) {
            throw new RenException(ErrorCode.SSIDS_EMPTY);
        }
        for (String ssid : deviceAddBindDTO.getSsids()) {
            // 检查mac是否已存在
            QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
            wrapper.eq("ssid", ssid);
            DeviceEntity exist = baseDao.selectOne(wrapper);
            if (exist != null) {
                throw new RenException(ErrorCode.SSID_ALREADY_EXISTS);
            }
            Date now = new Date();
            DeviceEntity entity = new DeviceEntity();
            BeanUtils.copyProperties(deviceAddBindDTO, entity);

            // 设置当前ssid相关信息
            entity.setDeviceSerialNumber(ssid.substring(17));
            LocalDate currentDate = LocalDate.now();
            entity.setDeviceYear(currentDate.getYear() + "");
            entity.setDeviceMonth(currentDate.getMonthValue() + "");
            entity.setSsid(ssid);
            entity.setCreateDate(now);
            entity.setUpdateDate(now);
            entity.setLastConnectedAt(now);
            entity.setCreator(deviceAddBindDTO.getUserId());
            entity.setUpdater(deviceAddBindDTO.getUserId());
            entity.setAutoUpdate(1);
            baseDao.insert(entity);
        }
        // 添加：清除智能体设备数量缓存
        redisUtils.delete(RedisKeys.getAgentDeviceCountById(deviceAddBindDTO.getAgentId()));
    }

    /**
     * 删除设备
     *
     * @param ssid 设备编码
     */
    @Override
    public void deleteDevice(String ssid) {
        // 先查询设备信息，获取agentId
        DeviceEntity device = this.getDeviceBySsid(ssid);
        if (device == null) {
            return;
        }
        if (StringUtils.isNotBlank(device.getAgentId())) {
            // 清除智能体设备数量缓存
            redisUtils.delete(RedisKeys.getAgentDeviceCountById(device.getAgentId()));
        }
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("ssid", ssid);
        baseDao.delete(wrapper);
    }


    /**
     * 设备状态改变
     *
     * @param ssid         设备编码
     * @param deviceStatus 设备状态
     */
    @Override
    public void deviceStatusChange(String ssid, boolean deviceStatus) {
        // 先查询设备信息，获取agentId
        DeviceEntity device = this.getDeviceBySsid(ssid);
        if (device == null) {
            return;
        }
        if (StringUtils.isNotBlank(device.getAgentId())) {
            // 清除智能体设备数量缓存
            redisUtils.delete(RedisKeys.getAgentDeviceCountById(device.getAgentId()));
        }
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        // 4、更新设备状态
        if (deviceStatus) {
            device.setDeviceStatus("0");
        } else {
            device.setDeviceStatus("1");
        }
        wrapper.eq("ssid", ssid);
        wrapper.set("device_status", device.getDeviceStatus());
        baseDao.update(wrapper);
    }

    /**
     * 设备详情信息
     *
     * @param ssid 设备编码
     * @return 设备详情信息
     */
    @Override
    public DeviceDetailVO deviceDetailInfo(String ssid) {
        DeviceEntity device = this.getDeviceBySsid(ssid);
        DeviceDetailVO deviceVO = new DeviceDetailVO();
        BeanUtils.copyProperties(device, deviceVO);
        if (device != null) {
            // 设备品牌
            List<SysDictDataItem> deviceBrand = dictDataService.getDictDataByType("device_brand");
            deviceVO.setDeviceBrandName(deviceBrand.stream().filter(item -> item.getKey().equals(device.getDeviceBrand())).findFirst().orElse(null).getName());
            // 设备渠道
            List<SysDictDataItem> deviceChannel = dictDataService.getDictDataByType("device_channel");
            deviceVO.setDeviceChannelName(deviceChannel.stream().filter(item -> item.getKey().equals(device.getDeviceChannel())).findFirst().orElse(null).getName());
            // 设备系列
            List<SysDictDataItem> deviceSeries = dictDataService.getDictDataByType("device_series");
            deviceVO.setDeviceSeriesName(deviceSeries.stream().filter(item -> item.getKey().equals(device.getDeviceSeries())).findFirst().orElse(null).getName());
            // 设备类型
            List<SysDictDataItem> deviceType = dictDataService.getDictDataByType("device_type");
            deviceVO.setDeviceTypeName(deviceType.stream().filter(item -> item.getKey().equals(device.getDeviceType())).findFirst().orElse(null).getName());
            // 设备型号
            List<SysDictDataItem> deviceModel = dictDataService.getDictDataByType("device_model");
            deviceVO.setDeviceModelName(deviceModel.stream().filter(item -> item.getKey().equals(device.getDeviceModel())).findFirst().orElse(null).getName());
            // 设备状态
            List<SysDictDataItem> deviceStatus = dictDataService.getDictDataByType("device_status");
            deviceVO.setDeviceStatusName(deviceStatus.stream().filter(item -> item.getKey().equals(device.getDeviceStatus())).findFirst().orElse(null).getName());
        }
        return deviceVO;
    }

    /**
     * 设备管理带参分页
     *
     * @param dto 分页查找参数
     * @return 设备列表分页数据
     */
    @Override
    public PageData<PageDeviceVO> page(PageDeviceDTO dto) {
        Map<String, Object> params = new HashMap<String, Object>();
        params.put(Constant.PAGE, dto.getPage());
        params.put(Constant.LIMIT, dto.getLimit());
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        if (dto.getDeviceStatus() != null) {
            wrapper.eq("device_status", dto.getDeviceStatus());
        }
        if (dto.getAgentId() != null) {
            wrapper.eq("agent_id", dto.getAgentId());
        }
        IPage<DeviceEntity> page = baseDao.selectPage(getPage(params, "create_date", false), wrapper);
        // 循环处理page获取回来的数据，返回需要的字段
        List<PageDeviceVO> list = page.getRecords().stream().map(device -> {
            PageDeviceVO deviceVO = new PageDeviceVO();
            BeanUtils.copyProperties(device, deviceVO);
            // 设备品牌
            List<SysDictDataItem> deviceBrand = dictDataService.getDictDataByType("device_brand");
            deviceVO.setDeviceBrandName(deviceBrand.stream().filter(item -> item.getKey().equals(device.getDeviceBrand())).findFirst().map(SysDictDataItem::getName).orElse(null));
            // 设备渠道
            List<SysDictDataItem> deviceChannel = dictDataService.getDictDataByType("device_channel");
            deviceVO.setDeviceChannelName(deviceChannel.stream().filter(item -> item.getKey().equals(device.getDeviceChannel())).findFirst().map(SysDictDataItem::getName).orElse(null));
            // 设备系列
            List<SysDictDataItem> deviceSeries = dictDataService.getDictDataByType("device_series");
            deviceVO.setDeviceSeriesName(deviceSeries.stream().filter(item -> item.getKey().equals(device.getDeviceSeries())).findFirst().map(SysDictDataItem::getName).orElse(null));
            // 设备类型
            List<SysDictDataItem> deviceType = dictDataService.getDictDataByType("device_type");
            deviceVO.setDeviceTypeName(deviceType.stream().filter(item -> item.getKey().equals(device.getDeviceType())).findFirst().map(SysDictDataItem::getName).orElse(null));
            // 设备型号
            List<SysDictDataItem> deviceModel = dictDataService.getDictDataByType("device_model");
            deviceVO.setDeviceModelName(deviceModel.stream().filter(item -> item.getKey().equals(device.getDeviceModel())).findFirst().map(SysDictDataItem::getName).orElse(null));
            // 设备状态
            List<SysDictDataItem> deviceStatus = dictDataService.getDictDataByType("device_status");
            deviceVO.setDeviceStatusName(deviceStatus.stream().filter(item -> item.getKey().equals(device.getDeviceStatus())).findFirst().map(SysDictDataItem::getName).orElse(null));
            return deviceVO;
        }).collect(Collectors.toList());
        return new PageData<>(list, page.getTotal());
    }

    /**
     * 生成设备码
     *
     * @param codeVO 用户生成设备编码的传入参数实体对象
     * @return 生成好的设备码
     */
    @Override
    public String generateDeviceCode(GenerateCodeVO codeVO) {
        // 使用synchronized确保多线程环境下的线程安全
        synchronized (this) {
            StringBuilder deviceCode = new StringBuilder();

            // 1. 添加品牌
            deviceCode.append(codeVO.getDeviceBrand());

            // 2. 添加系列
            deviceCode.append(codeVO.getDeviceSeries());

            // 3. 添加型号
            deviceCode.append(codeVO.getDeviceModel());

            // 4. 添加渠道代码
            deviceCode.append(codeVO.getDeviceChannel());

            // 5. 添加设备类型值
            deviceCode.append(codeVO.getDeviceType());

            LocalDate currentDate = LocalDate.now();

            // 6. 添加设备年份值
            deviceCode.append(currentDate.getYear());
            codeVO.setDeviceYear(String.valueOf(currentDate.getYear()));

            // 7. 计算月份代码
            // 获取月份
            // 获取当前月份的数字（例如，1代表一月，2代表二月，依此类推）
            int monthNumber = currentDate.getMonthValue();
            String monthCode = calculateMonthCode(String.valueOf(monthNumber));
            deviceCode.append(monthCode);
            codeVO.setDeviceMonth(String.valueOf(monthNumber));

            // 8. 获取并添加自增序号（8位，不足补0）
            Integer serialNumber = getNextSerialNumber(codeVO);

            deviceCode.append(String.format("%08d", serialNumber));

            return deviceCode.toString();
        }
    }

    /**
     * 批量生成设备码
     *
     * @param codeVO 用户生成设备编码的传入参数实体对象
     * @return 生成好的设备码
     */
    @Override
    public List<String> batchGenerateDeviceCode(GenerateCodeVO codeVO) {
        List<String> deviceCodes = new ArrayList<>();
        // 1、判断批量值是否传入
        if (Objects.isNull(codeVO)) {
            throw new RuntimeException("传入参数不能为空！");
        }
        if (Objects.isNull(codeVO.getDeviceBatchNum())) {
            throw new RuntimeException("传入批量数值参数不能为空！");
        }

        // 使用synchronized确保多线程环境下的线程安全
        synchronized (this) {
            LocalDate currentDate = LocalDate.now();

            // 构建设备码前缀
            StringBuilder prefixBuilder = new StringBuilder();
            prefixBuilder.append(codeVO.getDeviceBrand());
            prefixBuilder.append(codeVO.getDeviceSeries());
            prefixBuilder.append(codeVO.getDeviceModel());
            prefixBuilder.append(codeVO.getDeviceChannel());
            prefixBuilder.append(codeVO.getDeviceType());
            prefixBuilder.append(currentDate.getYear());

            // 计算月份代码
            int monthNumber = currentDate.getMonthValue();
            String monthCode = calculateMonthCodeFromMonthNumber(monthNumber);
            prefixBuilder.append(monthCode);

            String prefix = prefixBuilder.toString();

            // 获取起始序列号
            int startSerialNumber = createThisPrefixMaxDeviceCode(prefix);

            // 批量生成设备码
            for (int i = 0; i < codeVO.getDeviceBatchNum(); i++) {
                StringBuilder deviceCode = new StringBuilder(prefix);
                deviceCode.append(String.format("%08d", startSerialNumber + i));
                deviceCodes.add(deviceCode.toString());
            }
        }

        return deviceCodes;
    }

    /**
     * 计算月份代码
     * month_code = 季度代码(0起始) + A-L月份表达
     * 例如：三季度9月份为21
     *
     * @param deviceMonth 设备月份（格式：YYYY-MM 或 MM）
     * @return 月份代码
     */
    private String calculateMonthCode(String deviceMonth) {
        // 判断是否为空
        if (StringUtils.isEmpty(deviceMonth)) {
            // 如果没有提供月份，使用当前月份
            int currentMonth = java.time.LocalDate.now().getMonthValue();
            return calculateMonthCodeFromMonthNumber(currentMonth);
        }
        // 调取根据月份数字计算月份代码的逻辑
        return calculateMonthCodeFromMonthNumber(Integer.parseInt(deviceMonth));
    }

    /**
     * 根据月份数字计算月份代码
     *
     * @param month 月份数字（1-12）
     * @return 月份代码
     */
    private String calculateMonthCodeFromMonthNumber(int month) {
        // 计算季度（0起始）
        int quarter = (month - 1) / 3;

        // 月份字母表达（A-L对应1-12月）
        char monthLetter = (char) ('A' + month - 1);

        return quarter + String.valueOf(monthLetter);
    }

    /**
     * 获取下一个自增序号
     *
     * @param codeVO 设备码生成参数
     * @return 自增序号
     */
    private Integer getNextSerialNumber(GenerateCodeVO codeVO) {
        // 构建设备码前缀
        StringBuilder prefixBuilder = new StringBuilder();
        prefixBuilder.append(codeVO.getDeviceBrand());
        prefixBuilder.append(codeVO.getDeviceSeries());
        prefixBuilder.append(codeVO.getDeviceModel());
        prefixBuilder.append(codeVO.getDeviceChannel());
        prefixBuilder.append(codeVO.getDeviceType());
        prefixBuilder.append(codeVO.getDeviceYear());
        prefixBuilder.append(calculateMonthCode(codeVO.getDeviceMonth()));
        String prefix = prefixBuilder.toString();

        // 使用MyBatis-Plus查询数据库中最大的序列号
        return createThisPrefixMaxDeviceCode(prefix);
    }

    /**
     * 根据前缀查询该前缀下额的最大设备码，并查询数据库中最大的序列号
     *
     * @param prefix 设备码前缀
     * @return 返回
     */
    private synchronized int createThisPrefixMaxDeviceCode(String prefix) {
        Map<String, Object> resultMap = deviceDao.selectMap(prefix);
        Integer maxSerial = null;
        if (resultMap != null && !resultMap.isEmpty()) {
            if (resultMap.get("maxSerial") != null) {
                try {
                    maxSerial = Integer.parseInt(resultMap.get("maxSerial").toString());
                } catch (NumberFormatException e) {
                    log.warn("解析最大序列号失败，使用默认值1", e);
                }
            }
        }

        // 如果没有找到记录或解析失败，返回1，否则返回最大值+1
        return (maxSerial == null) ? 1 : (maxSerial + 1);
    }

    /**
     * 绑定设备蓝牙Id根据设备编码
     *
     * @param bluetoothIdDTO 绑定蓝牙id参数
     */
    @Override
    public void bindBluetoothIdBySsid(DeviceBindBluetoothIdDTO bluetoothIdDTO) {
        deviceDao.bindBluetoothIdBySsid(bluetoothIdDTO);
    }
}
