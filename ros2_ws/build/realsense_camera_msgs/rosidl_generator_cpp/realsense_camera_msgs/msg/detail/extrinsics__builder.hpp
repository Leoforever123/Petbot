// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from realsense_camera_msgs:msg/Extrinsics.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "realsense_camera_msgs/msg/extrinsics.hpp"


#ifndef REALSENSE_CAMERA_MSGS__MSG__DETAIL__EXTRINSICS__BUILDER_HPP_
#define REALSENSE_CAMERA_MSGS__MSG__DETAIL__EXTRINSICS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "realsense_camera_msgs/msg/detail/extrinsics__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace realsense_camera_msgs
{

namespace msg
{

namespace builder
{

class Init_Extrinsics_translation
{
public:
  explicit Init_Extrinsics_translation(::realsense_camera_msgs::msg::Extrinsics & msg)
  : msg_(msg)
  {}
  ::realsense_camera_msgs::msg::Extrinsics translation(::realsense_camera_msgs::msg::Extrinsics::_translation_type arg)
  {
    msg_.translation = std::move(arg);
    return std::move(msg_);
  }

private:
  ::realsense_camera_msgs::msg::Extrinsics msg_;
};

class Init_Extrinsics_rotation
{
public:
  explicit Init_Extrinsics_rotation(::realsense_camera_msgs::msg::Extrinsics & msg)
  : msg_(msg)
  {}
  Init_Extrinsics_translation rotation(::realsense_camera_msgs::msg::Extrinsics::_rotation_type arg)
  {
    msg_.rotation = std::move(arg);
    return Init_Extrinsics_translation(msg_);
  }

private:
  ::realsense_camera_msgs::msg::Extrinsics msg_;
};

class Init_Extrinsics_header
{
public:
  Init_Extrinsics_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Extrinsics_rotation header(::realsense_camera_msgs::msg::Extrinsics::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Extrinsics_rotation(msg_);
  }

private:
  ::realsense_camera_msgs::msg::Extrinsics msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::realsense_camera_msgs::msg::Extrinsics>()
{
  return realsense_camera_msgs::msg::builder::Init_Extrinsics_header();
}

}  // namespace realsense_camera_msgs

#endif  // REALSENSE_CAMERA_MSGS__MSG__DETAIL__EXTRINSICS__BUILDER_HPP_
