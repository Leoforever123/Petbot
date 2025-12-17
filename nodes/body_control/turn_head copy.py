import rclpy
from rclpy.lifecycle import LifecycleNode
from std_msgs.msg import String
import json
from body_controller import global_body_controller
import asyncio
from dotenv import load_dotenv

class TurnHeadNode(LifecycleNode):
    def __init__(self):
        super().__init__('turn_head')
        self.latest_msg = None  # 保存最新的消息
        self.message_count = 0  # 消息计数器
        self.face_detected_count = 0  # 检测到人脸的次数
        self.get_logger().info('=' * 60)
        self.get_logger().info('Turn Head Node 初始化完成')
        self.get_logger().info('=' * 60)

    def on_configure(self, state):
        self.controller = global_body_controller
        self.dead_zone = 0.02
        self.get_logger().info('配置阶段：设置死区为 {}'.format(self.dead_zone))
        self.get_logger().info('配置阶段：初始化头部位置（向上0.34度）')
        self.controller.yhead('up', 0.34, blocking=False, mode='relative') 
        self.get_logger().info('配置完成！')
        return super().on_configure(state)
        
    def on_activate(self, state):
        self.subscription = self.create_subscription(
            String,
            'face_recognition_result',
            self._subscription_callback,
            10)
        self.get_logger().info('=' * 60)
        self.get_logger().info('✅ 节点已激活！开始监听话题: /face_recognition_result')
        self.get_logger().info('=' * 60)
        return super().on_activate(state)
    
    def on_deactivate(self, state):
        self.get_logger().info('节点停用中，重置机器人身体...')
        self.controller.reset_body()
        self.destroy_subscription(self.subscription)
        self.get_logger().info('节点已停用')
        return super().on_deactivate(state)
    
    def _subscription_callback(self, msg):
        # 保存最新的消息
        self.latest_msg = msg
        self.message_count += 1
        
        # 每收到10条消息输出一次统计
        if self.message_count % 10 == 0:
            self.get_logger().info('📊 统计: 已接收 {} 条消息，检测到人脸 {} 次'.format(
                self.message_count, self.face_detected_count))

    async def listener_callback(self, msg):
        try:
            faces = json.loads(msg.data)
            
            if len(faces) == 0:
                # 没有检测到人脸
                self.get_logger().debug('📭 未检测到人脸')
                return
            
            # 检测到人脸
            self.face_detected_count += 1
            num_faces = len(faces)
            
            self.get_logger().info('=' * 60)
            self.get_logger().info('👤 检测到 {} 张人脸！'.format(num_faces))
            
            # 使用第一张人脸
            face = faces[0]
            location = face['location']
            
            # 计算人脸中心
            y = (location[0] + location[2]) / 2  # top 和 bottom 的平均
            x = (location[1] + location[3]) / 2  # left 和 right 的平均
            
            # 计算图像中心位置（320x240是图像中心）
            image_center_x = 320
            image_center_y = 240
            
            self.get_logger().info('📍 人脸位置:')
            self.get_logger().info('   - 矩形框: top={}, left={}, bottom={}, right={}'.format(
                location[0], location[1], location[2], location[3]))
            self.get_logger().info('   - 中心点: x={:.1f}, y={:.1f}'.format(x, y))
            self.get_logger().info('   - 图像中心: x={}, y={}'.format(image_center_x, image_center_y))
            
            # 计算误差（归一化到 -0.5 ~ 0.5）
            x_error = (x - image_center_x) / 640
            y_error = (y - image_center_y) / 480
            
            self.get_logger().info('📐 计算误差:')
            self.get_logger().info('   - X轴误差: {:.4f} ({}偏移 {:.1f} 像素)'.format(
                x_error, 
                '右' if x_error > 0 else '左',
                abs(x_error * 640)))
            self.get_logger().info('   - Y轴误差: {:.4f} ({}偏移 {:.1f} 像素)'.format(
                y_error,
                '下' if y_error > 0 else '上',
                abs(y_error * 480)))
            self.get_logger().info('   - 死区阈值: {:.4f}'.format(self.dead_zone))
            
            # 应用死区
            x_error_original = x_error
            y_error_original = y_error
            
            if abs(x_error) < self.dead_zone:
                x_error = 0
            if abs(y_error) < self.dead_zone:
                y_error = 0
            
            # 控制头部移动
            moved = False
            
            if x_error != 0:
                direction = 'left' if x_error < 0 else 'right'
                angle = abs(x_error) * 20
                self.get_logger().info('🔄 X轴控制:')
                self.get_logger().info('   - 方向: {}'.format(direction))
                self.get_logger().info('   - 角度: {:.2f}°'.format(angle))
                self.get_logger().info('   - 执行: async_xhead("{}", {:.2f}, blocking=False, mode="relative")'.format(
                    direction, angle))
                await self.controller.async_xhead(direction, angle, blocking=False, mode='relative')
                moved = True
            else:
                if abs(x_error_original) > 0:
                    self.get_logger().info('⏸️  X轴: 在死区内 (误差={:.4f} < {:.4f})，不移动'.format(
                        abs(x_error_original), self.dead_zone))
                else:
                    self.get_logger().info('✅ X轴: 已对齐中心')
                    
            if y_error != 0:
                direction = 'up' if y_error < 0 else 'down'
                angle = abs(y_error) * 10
                self.get_logger().info('🔄 Y轴控制:')
                self.get_logger().info('   - 方向: {}'.format(direction))
                self.get_logger().info('   - 角度: {:.2f}°'.format(angle))
                self.get_logger().info('   - 执行: async_yhead("{}", {:.2f}, blocking=False, mode="relative")'.format(
                    direction, angle))
                await self.controller.async_yhead(direction, angle, blocking=False, mode='relative')
                moved = True
            else:
                if abs(y_error_original) > 0:
                    self.get_logger().info('⏸️  Y轴: 在死区内 (误差={:.4f} < {:.4f})，不移动'.format(
                        abs(y_error_original), self.dead_zone))
                else:
                    self.get_logger().info('✅ Y轴: 已对齐中心')
            
            if not moved:
                self.get_logger().info('🎯 人脸已居中，无需移动')
            
            self.get_logger().info('=' * 60)
            
        except json.JSONDecodeError as e:
            self.get_logger().error('❌ JSON解析错误: {}'.format(e))
        except KeyError as e:
            self.get_logger().error('❌ 数据格式错误，缺少键: {}'.format(e))
        except Exception as e:
            self.get_logger().error('❌ 处理人脸数据时出错: {}'.format(e))
            import traceback
            self.get_logger().error(traceback.format_exc())

def main(args=None):
    rclpy.init(args=args)
    node = TurnHeadNode()

    # 创建新的事件循环
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    print('=' * 60)
    print('🚀 Turn Head Node 主循环启动')
    print('=' * 60)

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)  # 非阻塞spin

            if node.latest_msg is not None:
                msg = node.latest_msg
                node.latest_msg = None  # 处理完清空
                try:
                    loop.run_until_complete(node.listener_callback(msg))
                except Exception as e:
                    node.get_logger().error('❌ 执行listener_callback时出错: {}'.format(e))
                    import traceback
                    node.get_logger().error(traceback.format_exc())

    except KeyboardInterrupt:
        print('\n🛑 收到中断信号，正在关闭...')
    finally:
        node.destroy_node()
        rclpy.shutdown()
        loop.close()
        print('✅ 节点已安全关闭')

if __name__ == '__main__':
    load_dotenv()
    main()
