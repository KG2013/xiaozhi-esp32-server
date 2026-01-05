from http.server import BaseHTTPRequestHandler
import json
from typing import Dict, Any

from core.api.base_handler import BaseHandler
from core.device.models import DeviceCodeParams
from core.device.device_service import device_service

class DeviceHandler(BaseHandler):
    """
    设备相关API处理器
    负责处理设备编码生成等请求
    """
    
    def do_POST(self):
        """
        处理POST请求
        """
        if self.path == '/api/device/generateDeviceCode' or self.path == '/api/device/batchGenerateDeviceCode':
            self._handle_generate_device_code()
        else:
            self.send_error(404, "Not Found")
    
    def _handle_generate_device_code(self):
        """
        处理生成设备编码的请求
        
        请求体格式：
        {
            "roleId": 1,
            "deviceBrand": "品牌",
            "channel": "渠道",
            "deviceSeries": "系列",
            "deviceType": "类型",
            "deviceModel": "型号",
            "year": 2024,
            "month": 11,
            "batchSize": 1
        }
        """
        try:
            # 获取请求体
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            
            # 解析JSON
            request_data = json.loads(body)
            
            # 转换为参数对象
            params = self._parse_device_code_params(request_data)
            
            # 验证参数
            params.validate()
            
            # 根据是否批量生成调用相应方法
            if params.batch_size > 1:
                # 批量生成
                device_codes = device_service.batch_generate_device_codes(params)
                result = {
                    "code": 200,
                    "msg": "success",
                    "data": device_codes
                }
            else:
                # 生成单个编码
                device_code = device_service.generate_device_code(params)
                result = {
                    "code": 200,
                    "msg": "success",
                    "data": device_code
                }
            
            # 返回结果
            self._send_json_response(result)
            
        except json.JSONDecodeError:
            self._send_error_response(400, "请求体格式错误")
        except ValueError as e:
            self._send_error_response(400, str(e))
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"生成设备编码失败: {str(e)}")
            self._send_error_response(500, "服务器内部错误")
    
    def _parse_device_code_params(self, request_data: Dict[str, Any]) -> DeviceCodeParams:
        """
        从请求数据解析设备编码参数
        
        Args:
            request_data: 请求数据
            
        Returns:
            DeviceCodeParams: 设备编码参数对象
        """
        # 转换驼峰命名为下划线命名
        mapping = {
            'roleId': 'role_id',
            'deviceBrand': 'device_brand',
            'deviceSeries': 'device_series',
            'deviceType': 'device_type',
            'deviceModel': 'device_model',
            'batchSize': 'batch_size'
        }
        
        parsed_data = {}
        for key, value in request_data.items():
            if key in mapping:
                parsed_data[mapping[key]] = value
            else:
                parsed_data[key] = value
        
        # 创建参数对象
        return DeviceCodeParams(**parsed_data)
    
    def _send_json_response(self, data: Dict[str, Any]):
        """
        发送JSON响应
        
        Args:
            data: 要返回的数据
        """
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 将数据转换为JSON字符串并发送
        response_json = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_error_response(self, status_code: int, message: str):
        """
        发送错误响应
        
        Args:
            status_code: HTTP状态码
            message: 错误消息
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_data = {
            "code": status_code,
            "msg": message,
            "data": None
        }
        response_json = json.dumps(error_data, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))
    
    def do_OPTIONS(self):
        """
        处理跨域OPTIONS请求
        """
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()