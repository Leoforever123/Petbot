// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from realsense_camera_msgs:msg/Extrinsics.idl
// generated code does not contain a copyright notice
#include "realsense_camera_msgs/msg/detail/extrinsics__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
realsense_camera_msgs__msg__Extrinsics__init(realsense_camera_msgs__msg__Extrinsics * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    realsense_camera_msgs__msg__Extrinsics__fini(msg);
    return false;
  }
  // rotation
  // translation
  return true;
}

void
realsense_camera_msgs__msg__Extrinsics__fini(realsense_camera_msgs__msg__Extrinsics * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // rotation
  // translation
}

bool
realsense_camera_msgs__msg__Extrinsics__are_equal(const realsense_camera_msgs__msg__Extrinsics * lhs, const realsense_camera_msgs__msg__Extrinsics * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // rotation
  for (size_t i = 0; i < 9; ++i) {
    if (lhs->rotation[i] != rhs->rotation[i]) {
      return false;
    }
  }
  // translation
  for (size_t i = 0; i < 3; ++i) {
    if (lhs->translation[i] != rhs->translation[i]) {
      return false;
    }
  }
  return true;
}

bool
realsense_camera_msgs__msg__Extrinsics__copy(
  const realsense_camera_msgs__msg__Extrinsics * input,
  realsense_camera_msgs__msg__Extrinsics * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // rotation
  for (size_t i = 0; i < 9; ++i) {
    output->rotation[i] = input->rotation[i];
  }
  // translation
  for (size_t i = 0; i < 3; ++i) {
    output->translation[i] = input->translation[i];
  }
  return true;
}

realsense_camera_msgs__msg__Extrinsics *
realsense_camera_msgs__msg__Extrinsics__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  realsense_camera_msgs__msg__Extrinsics * msg = (realsense_camera_msgs__msg__Extrinsics *)allocator.allocate(sizeof(realsense_camera_msgs__msg__Extrinsics), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(realsense_camera_msgs__msg__Extrinsics));
  bool success = realsense_camera_msgs__msg__Extrinsics__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
realsense_camera_msgs__msg__Extrinsics__destroy(realsense_camera_msgs__msg__Extrinsics * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    realsense_camera_msgs__msg__Extrinsics__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
realsense_camera_msgs__msg__Extrinsics__Sequence__init(realsense_camera_msgs__msg__Extrinsics__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  realsense_camera_msgs__msg__Extrinsics * data = NULL;

  if (size) {
    data = (realsense_camera_msgs__msg__Extrinsics *)allocator.zero_allocate(size, sizeof(realsense_camera_msgs__msg__Extrinsics), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = realsense_camera_msgs__msg__Extrinsics__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        realsense_camera_msgs__msg__Extrinsics__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
realsense_camera_msgs__msg__Extrinsics__Sequence__fini(realsense_camera_msgs__msg__Extrinsics__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      realsense_camera_msgs__msg__Extrinsics__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

realsense_camera_msgs__msg__Extrinsics__Sequence *
realsense_camera_msgs__msg__Extrinsics__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  realsense_camera_msgs__msg__Extrinsics__Sequence * array = (realsense_camera_msgs__msg__Extrinsics__Sequence *)allocator.allocate(sizeof(realsense_camera_msgs__msg__Extrinsics__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = realsense_camera_msgs__msg__Extrinsics__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
realsense_camera_msgs__msg__Extrinsics__Sequence__destroy(realsense_camera_msgs__msg__Extrinsics__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    realsense_camera_msgs__msg__Extrinsics__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
realsense_camera_msgs__msg__Extrinsics__Sequence__are_equal(const realsense_camera_msgs__msg__Extrinsics__Sequence * lhs, const realsense_camera_msgs__msg__Extrinsics__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!realsense_camera_msgs__msg__Extrinsics__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
realsense_camera_msgs__msg__Extrinsics__Sequence__copy(
  const realsense_camera_msgs__msg__Extrinsics__Sequence * input,
  realsense_camera_msgs__msg__Extrinsics__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(realsense_camera_msgs__msg__Extrinsics);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    realsense_camera_msgs__msg__Extrinsics * data =
      (realsense_camera_msgs__msg__Extrinsics *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!realsense_camera_msgs__msg__Extrinsics__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          realsense_camera_msgs__msg__Extrinsics__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!realsense_camera_msgs__msg__Extrinsics__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
