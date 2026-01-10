#!/usr/bin/env python3
"""
Weather Query Tool - 天气查询工具
使用高德地图API查询天气信息
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class WeatherTool:
    """天气查询工具类"""
    
    def __init__(self):
        """初始化天气查询工具"""
        self.amap_key = os.getenv('AMAP_API_KEY')
        if not self.amap_key:
            print("⚠️  警告: 未找到高德地图API密钥 (AMAP_API_KEY)")
            print("   天气查询功能将不可用")
        
        # 高德地图API端点
        self.geocode_url = "https://restapi.amap.com/v3/geocode/geo"
        self.weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    def get_city_code(self, city_name: str) -> Optional[str]:
        """
        获取城市的adcode
        
        Args:
            city_name: 城市名称（如：北京、上海）
            
        Returns:
            城市adcode，失败返回None
        """
        if not self.amap_key:
            return None
        
        try:
            params = {
                'key': self.amap_key,
                'address': city_name,
                'city': city_name
            }
            
            response = requests.get(self.geocode_url, params=params, timeout=5)
            data = response.json()
            
            if data['status'] == '1' and data['geocodes']:
                adcode = data['geocodes'][0]['adcode']
                return adcode
            else:
                return None
                
        except Exception as e:
            print(f"获取城市代码失败: {e}")
            return None
    
    def get_weather(self, city_name: str) -> Dict[str, Any]:
        """
        查询指定城市的天气
        
        Args:
            city_name: 城市名称（如：北京、上海）
            
        Returns:
            天气信息字典
        """
        if not self.amap_key:
            return {
                'success': False,
                'error': '未配置高德地图API密钥',
                'message': '请设置 AMAP_API_KEY 环境变量'
            }
        
        try:
            # 1. 获取城市adcode
            adcode = self.get_city_code(city_name)
            if not adcode:
                return {
                    'success': False,
                    'error': '城市不存在',
                    'message': f'无法找到城市: {city_name}'
                }
            
            # 2. 查询天气
            params = {
                'key': self.amap_key,
                'city': adcode,
                'extensions': 'base'  # base=实况天气, all=预报天气
            }
            
            response = requests.get(self.weather_url, params=params, timeout=5)
            data = response.json()
            
            if data['status'] == '1' and data['lives']:
                live = data['lives'][0]
                return {
                    'success': True,
                    'city': live['province'] + live['city'],
                    'weather': live['weather'],
                    'temperature': live['temperature'] + '°C',
                    'winddirection': live['winddirection'] + '风',
                    'windpower': live['windpower'] + '级',
                    'humidity': live['humidity'] + '%',
                    'reporttime': live['reporttime'],
                    'message': self._format_weather_message(live)
                }
            else:
                return {
                    'success': False,
                    'error': '查询失败',
                    'message': f'无法获取 {city_name} 的天气信息'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'天气查询出错: {str(e)}'
            }
    
    def _format_weather_message(self, weather_data: Dict) -> str:
        """
        格式化天气信息为自然语言
        
        Args:
            weather_data: 天气数据
            
        Returns:
            格式化后的天气描述
        """
        city = weather_data['city']
        weather = weather_data['weather']
        temp = weather_data['temperature']
        wind = weather_data['winddirection']
        power = weather_data['windpower']
        
        message = f"{city}当前天气{weather}，气温{temp}度，{wind}{power}级"
        return message


# 提供给LangGraph使用的工具函数
def query_weather(city: str) -> str:
    """
    查询天气的工具函数（LangGraph格式）
    
    Args:
        city: 城市名称
        
    Returns:
        天气信息的文字描述
    """
    tool = WeatherTool()
    result = tool.get_weather(city)
    
    if result['success']:
        return result['message']
    else:
        return result['message']


# 测试代码
if __name__ == '__main__':
    tool = WeatherTool()
    
    # 测试查询北京天气
    print("测试查询北京天气:")
    result = tool.get_weather("北京")
    print(f"结果: {result}")
    print()
    
    # 测试查询上海天气
    print("测试查询上海天气:")
    result = tool.get_weather("上海")
    print(f"结果: {result}")
    print()
    
    # 使用工具函数
    print("使用工具函数查询深圳天气:")
    message = query_weather("深圳")
    print(f"消息: {message}")


