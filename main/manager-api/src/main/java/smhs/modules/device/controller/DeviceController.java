package smhs.modules.device.controller;

import java.util.List;
import java.util.Map;

import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import org.apache.commons.lang3.ObjectUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.beans.BeanUtils;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import smhs.common.constant.Constant;
import smhs.common.exception.ErrorCode;
import smhs.common.page.PageData;
import smhs.common.redis.RedisKeys;
import smhs.common.redis.RedisUtils;
import smhs.common.user.UserDetail;
import smhs.common.utils.Result;
import smhs.common.validator.ValidatorUtils;
import smhs.modules.device.dto.*;
import smhs.modules.device.entity.DeviceEntity;
import smhs.modules.device.service.DeviceService;
import smhs.modules.device.vo.DeviceDetailVO;
import smhs.modules.device.vo.GenerateCodeVO;
import smhs.modules.device.vo.PageDeviceVO;
import smhs.modules.security.user.SecurityUser;
import smhs.modules.sys.dto.AdminPageUserDTO;
import smhs.modules.sys.service.SysParamsService;
import smhs.modules.sys.vo.AdminPageUserVO;

@Tag(name = "设备管理")
@RestController
@RequestMapping("/device")
public class DeviceController {

    private final DeviceService deviceService;
    private final RedisUtils redisUtils;
    private final SysParamsService sysParamsService;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    public DeviceController(DeviceService deviceService, RedisUtils redisUtils, SysParamsService sysParamsService, RestTemplate restTemplate, ObjectMapper objectMapper) {
        this.deviceService = deviceService;
        this.redisUtils = redisUtils;
        this.sysParamsService = sysParamsService;
        this.restTemplate = restTemplate;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/bind/{agentId}/{deviceCode}")
    @Operation(summary = "绑定设备")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> bindDevice(@PathVariable String agentId, @PathVariable String deviceCode) {
        deviceService.deviceActivation(agentId, deviceCode);
        return new Result<>();
    }

    @PostMapping("/register")
    @Operation(summary = "注册设备")
    public Result<String> registerDevice(@RequestBody DeviceRegisterDTO deviceRegisterDTO) {
        String macAddress = deviceRegisterDTO.getMacAddress();
        if (StringUtils.isBlank(macAddress)) {
            return new Result<String>().error(ErrorCode.NOT_NULL, "mac地址不能为空");
        }
        // 生成六位验证码
        String code = String.valueOf(Math.random()).substring(2, 8);
        String key = RedisKeys.getDeviceCaptchaKey(code);
        String existsMac = null;
        do {
            existsMac = (String) redisUtils.get(key);
        } while (StringUtils.isNotBlank(existsMac));

        redisUtils.set(key, macAddress);
        return new Result<String>().ok(code);
    }

    @GetMapping("/bind/{agentId}")
    @Operation(summary = "获取已绑定设备")
    @RequiresPermissions("sys:role:normal")
    public Result<List<DeviceEntity>> getUserDevices(@PathVariable String agentId) {
        UserDetail user = SecurityUser.getUser();
        List<DeviceEntity> devices = deviceService.getUserDevices(user.getId(), agentId);
        return new Result<List<DeviceEntity>>().ok(devices);
    }

    @PostMapping("/bind/{agentId}")
    @Operation(summary = "设备在线接口")
    @RequiresPermissions("sys:role:normal")
    public Result<String> forwardToMqttGateway(@PathVariable String agentId, @RequestBody String requestBody) {
        try {
            // 从系统参数中获取MQTT网关地址
            String mqttGatewayUrl = sysParamsService.getValue("server.mqtt_manager_api", true);
            if (StringUtils.isBlank(mqttGatewayUrl) || "null".equals(mqttGatewayUrl)) {
                return new Result<>();
            }

            // 获取当前用户的设备列表
            UserDetail user = SecurityUser.getUser();
            List<DeviceEntity> devices = deviceService.getUserDevices(user.getId(), agentId);

            // 构建deviceIds数组
            java.util.List<String> deviceIds = new java.util.ArrayList<>();
            for (DeviceEntity device : devices) {
                String macAddress = device.getMacAddress() != null ? device.getMacAddress() : "unknown";
                String groupId = device.getBoard() != null ? device.getBoard() : "GID_default";

                // 替换冒号为下划线
                groupId = groupId.replace(":", "_");
                macAddress = macAddress.replace(":", "_");

                // 构建mqtt客户端ID格式：groupId@@@macAddress@@@macAddress
                String mqttClientId = groupId + "@@@" + macAddress + "@@@" + macAddress;
                deviceIds.add(mqttClientId);
            }

            // 构建完整的URL
            String url = "http://" + mqttGatewayUrl + "/api/devices/status";

            // 设置请求头
            HttpHeaders headers = new HttpHeaders();
            headers.set("Content-Type", "application/json");

            // 生成Bearer令牌
            String token = generateBearerToken();
            if (token == null) {
                return new Result<String>().error("令牌生成失败");
            }
            headers.set("Authorization", "Bearer " + token);

            // 构建请求体JSON
            String jsonBody = "{\"clientIds\":" + objectMapper.writeValueAsString(deviceIds) + "}";
            HttpEntity<String> requestEntity = new HttpEntity<>(jsonBody, headers);

            // 发送POST请求
            ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.POST, requestEntity, String.class);

            // 返回响应
            return new Result<String>().ok(response.getBody());
        } catch (Exception e) {
            return new Result<String>().error("转发请求失败: " + e.getMessage());
        }
    }

    private String generateBearerToken() {
        try {
            // 获取当前日期，格式为yyyy-MM-dd
            String dateStr = java.time.LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd"));

            // 获取MQTT签名密钥
            String signatureKey = sysParamsService.getValue("server.mqtt_signature_key", false);
            if (StringUtils.isBlank(signatureKey)) {
                return null;
            }

            // 将日期字符串与MQTT_SIGNATURE_KEY连接
            String tokenContent = dateStr + signatureKey;

            // 对连接后的字符串进行SHA256哈希计算
            String token = org.apache.commons.codec.digest.DigestUtils.sha256Hex(tokenContent);

            return token;
        } catch (Exception e) {
            return null;
        }
    }

    @PostMapping("/unbind")
    @Operation(summary = "解绑设备")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> unbindDevice(@RequestBody DeviceUnBindDTO unDeviveBind) {
        UserDetail user = SecurityUser.getUser();
        deviceService.unbindDevice(user.getId(), unDeviveBind.getDeviceId());
        return new Result<Void>();
    }

    @PutMapping("/update/{id}")
    @Operation(summary = "更新设备信息")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> updateDeviceInfo(@PathVariable String id, @Valid @RequestBody DeviceUpdateDTO deviceUpdateDTO) {
        DeviceEntity entity = deviceService.selectById(id);
        if (entity == null) {
            return new Result<Void>().error("设备不存在");
        }
        UserDetail user = SecurityUser.getUser();
        if (!entity.getUserId().equals(user.getId())) {
            return new Result<Void>().error("设备不存在");
        }
        BeanUtils.copyProperties(deviceUpdateDTO, entity);
        deviceService.updateById(entity);
        return new Result<Void>();
    }

    @PostMapping("/manual-add")
    @Operation(summary = "手动添加设备")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> manualAddDevice(@RequestBody @Valid DeviceManualAddDTO dto) {
        UserDetail user = SecurityUser.getUser();
        deviceService.manualAddDevice(user.getId(), dto);
        return new Result<>();
    }

    @PostMapping("/addBindDevice")
    @Operation(summary = "添加设备")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> addBindDevice(@RequestBody @Valid DeviceAddBindDTO dto) {
        UserDetail user = SecurityUser.getUser();
        dto.setUserId(user.getId());
        deviceService.addBindDevice(dto);
        return new Result<>();
    }

    @Operation(summary = "批量删除设备")
    @PostMapping("/deleteDevice")
    @RequiresPermissions("sys:role:normal")
    @Parameters({
            @Parameter(name = "ssids", description = "需要删除的设备编码数据集", ref = "List<String>"),
    })
    public Result<Void> deleteDevice(@RequestBody List<String> ssids) {
        if (ObjectUtils.isEmpty(ssids)) {
            return new Result<Void>().error("请选择要删除的设备");
        }
        for (String ssid : ssids) {
            DeviceEntity device = deviceService.getDeviceBySsid(ssid);
            if (device == null) {
                return new Result<Void>().error("您要删除的设备不存在！");
            }
            if (device.getDeviceStatus().equals("0")) {
                return new Result<Void>().error("您要删除的设备号：{" + ssid + "},已经启用无法删除！");
            }
            deviceService.deleteDevice(ssid);
            return new Result<>();
        }
        return new Result<>();
    }

    @GetMapping("/pageDevice")
    @Operation(summary = "设备管理带参分页")
    @RequiresPermissions("sys:role:normal")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "当前页码，从1开始", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.LIMIT, description = "每页显示记录数", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.ORDER_FIELD, description = "排序字段", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = Constant.ORDER, description = "排序方式，可选值(asc、desc)", in = ParameterIn.QUERY, ref = "String")
    })
    public Result<PageData<PageDeviceVO>> pageDevice(@Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        PageDeviceDTO dto = new PageDeviceDTO();
        dto.setLimit((String) params.get(Constant.LIMIT));
        dto.setPage((String) params.get(Constant.PAGE));
        dto.setAgentId((String) params.get("agentId"));
        ValidatorUtils.validateEntity(dto);
        PageData<PageDeviceVO> page = deviceService.page(dto);
        return new Result<PageData<PageDeviceVO>>().ok(page);
    }

    @GetMapping("/wechatPageDevice")
    @Operation(summary = "仅供微信小程序使用 - 设备管理带参分页")
    @RequiresPermissions("sys:role:normal")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "当前页码，从1开始", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.LIMIT, description = "每页显示记录数", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.ORDER_FIELD, description = "排序字段", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = Constant.ORDER, description = "排序方式，可选值(asc、desc)", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = "deviceStatus", description = "设备状态:（0：已启用，1：已禁用 ）", in = ParameterIn.QUERY, ref = "String")
    })
    public Result<PageData<PageDeviceVO>> wechatPageDevice(@Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        PageDeviceDTO dto = new PageDeviceDTO();
        dto.setLimit((String) params.get(Constant.LIMIT));
        dto.setPage((String) params.get(Constant.PAGE));
        if(params.get("deviceStatus")!=null){
            dto.setDeviceStatus((String) params.get("deviceStatus"));
        }else{
            dto.setDeviceStatus(null);
        }
        ValidatorUtils.validateEntity(dto);
        PageData<PageDeviceVO> page = deviceService.page(dto);
        return new Result<PageData<PageDeviceVO>>().ok(page);
    }


    @Operation(summary = "生成设备码")
    @PostMapping("/generateDeviceCode")
    @RequiresPermissions("sys:role:normal")
    public Result<String> generateDeviceCode(@RequestBody @Valid GenerateCodeVO deviceCode) {
        return new Result<String>().ok(deviceService.generateDeviceCode(deviceCode));
    }

    @Operation(summary = "批量生成设备码")
    @PostMapping("/batchGenerateDeviceCode")
    @RequiresPermissions("sys:role:normal")
    public Result<List<String>> batchGenerateDeviceCode(@RequestBody @Valid GenerateCodeVO deviceCode) {
        return new Result<List<String>>().ok(deviceService.batchGenerateDeviceCode(deviceCode));
    }

    /**
     * 设备状态批量处理
     *
     * @param ssids 设备编码数据集
     * @return Result<Void>
     */
    @Operation(summary = "批量设备启用/禁用")
    @PostMapping("/batchEnable")
    @RequiresPermissions("sys:role:normal")
    @Parameters({
            @Parameter(name = "ssids", description = "需要启用/禁用的设备编码数据集", ref = "List<String>"),
            @Parameter(name = "enable", description = "需要启用/禁用的设备编码状态(启用：true/禁用：false)", ref = "Boolean")
    })
    public Result<Void> batchEnable(@RequestParam List<String> ssids, @RequestParam Boolean enable) {
        for (String ssid : ssids) {
            deviceService.deviceStatusChange(ssid, enable);
        }
        return new Result<>();
    }

    @GetMapping("/detail/{ssid}")
    @Operation(summary = "获取设备详情信息")
    @RequiresPermissions("sys:role:normal")
    public Result<DeviceDetailVO> deviceDetailInfo(@PathVariable String ssid) {
        DeviceDetailVO deviceDetailInfo = deviceService.deviceDetailInfo(ssid);
        return new Result<DeviceDetailVO>().ok(deviceDetailInfo);
    }

    @PostMapping("/bindBluetoothIdBySsid")
    @Operation(summary = "绑定设备蓝牙Id根据设备编码")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> bindBluetoothIdBySsid(@PathVariable DeviceBindBluetoothIdDTO  bluetoothIdDTO) {
        deviceService.bindBluetoothIdBySsid(bluetoothIdDTO);
        return new Result<>();
    }
}