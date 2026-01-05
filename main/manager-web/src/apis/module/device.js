import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

export default {
    // 已绑设备
    getAgentBindDevices(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/bind/${agentId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('获取设备列表失败:', err);
                RequestService.reAjaxFun(() => {
                    this.getAgentBindDevices(agentId, callback);
                });
            }).send();
    },
    // 解绑设备
    unbindDevice(device_id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/unbind`)
            .method('POST')
            .data({ deviceId: device_id })
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('解绑设备失败:', err);
                RequestService.reAjaxFun(() => {
                    this.unbindDevice(device_id, callback);
                });
            }).send();
    },
    // 绑定设备
    bindDevice(agentId, deviceCode, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/bind/${agentId}/${deviceCode}`)
            .method('POST')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('绑定设备失败:', err);
                RequestService.reAjaxFun(() => {
                    this.bindDevice(agentId, deviceCode, callback);
                });
            }).send();
    },
    updateDeviceInfo(id, payload, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/update/${id}`)
            .method('PUT')
            .data(payload)
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('更新OTA状态失败:', err)
                this.$message.error(err.msg || '更新OTA状态失败')
                RequestService.reAjaxFun(() => {
                    this.updateDeviceInfo(id, payload, callback)
                })
            }).send()
    },
    // 手动添加设备
    manualAddDevice(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/manual-add`)
            .method('POST')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('手动添加设备失败:', err);
                RequestService.reAjaxFun(() => {
                    this.manualAddDevice(params, callback);
                });
            }).send();
    },
    // 获取设备状态
    getDeviceStatus(agentId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/bind/${agentId}`)
            .method('POST')
            .data({}) // 发送空对象作为请求体
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('获取设备状态失败:', err);
                RequestService.reAjaxFun(() => {
                    this.getDeviceStatus(agentId, callback);
                });
            }).send();
    },
    // 生成设备码
    getDeviceCode(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/generateDeviceCode`)
            .method('POST')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('生成设备码失败:', err);
                RequestService.reAjaxFun(() => {
                    this.getDeviceCode(params, callback);
                });
            }).send();
    },
    // 批量生成设备码
    getBatchDeviceCode(params, callback){
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/batchGenerateDeviceCode`)
            .method('POST')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('批量生成设备码失败:', err);
                RequestService.reAjaxFun(() => {
                    this.getBatchDeviceCode(params, callback);
                });
            }).send();
    },
    // 添加设备
    addBindDevice(params, callback){
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/addBindDevice`)
            .method('POST')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('生成设备码失败:', err);
                RequestService.reAjaxFun(() => {
                    this.addBindDevice(params, callback);
                });
            }).send();
    },
    // 获取页面列表
    getNewListData(params, callback) {
        const queryParams = new URLSearchParams({
            page: params.page,
            limit: params.limit,
            agentId:params.agentId
        }).toString();
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/pageDevice?${queryParams}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime()
                callback(res)
            })
            .networkFail((err) => {
                console.error('获取参数列表失败:', err)
                RequestService.reAjaxFun(() => {
                    this.getNewListData(params, callback)
                })
            }).send()
    },
    newDeleteDevice(params, callback){
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/deleteDevice`)
            .method('POST')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('删除设备失败:', err);
                RequestService.reAjaxFun(() => {
                    this.deleteDevice(params, callback);
                });
            }).send();
    },
    getDeviceDetail(params, callback){
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/detail/${params}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('获取设备详情失败:', err);
                RequestService.reAjaxFun(() => {
                    this.getDeviceDetail(params, callback);
                });
            }).send();
    },
    devicebatchEnable(params, callback){
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/device/batchEnable?${params}`)
            .method('POST')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('启用/禁用失败:', err);
                RequestService.reAjaxFun(() => {
                    this.devicebatchEnable(params, callback);
                });
            }).send();
    }
}