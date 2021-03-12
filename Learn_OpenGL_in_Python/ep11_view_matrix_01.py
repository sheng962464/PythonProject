# -*- encoding: utf-8 -*-
"""
视图变换矩阵
"""

from io import BytesIO

import glfw
import numpy as np
import pyrr
import requests
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image


def window_resize(width, height):
    """
    窗口调整大小
    """
    glViewport(0, 0, width, height)


# 增加 view 矩阵
# 这里三个变换矩阵齐了之后梳理一下关系
# https://learnopengl-cn.github.io/01%20Getting%20started/08%20Coordinate%20Systems/
# 先模型矩阵，再视角矩阵，再投影矩阵
# 局部空间 ——（model）—— 世界空间 ——（view）—— 观察空间 ——（projection）—— 裁减空间
vertex_src = """
# version 330

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec2 a_texture;

uniform mat4 model;  // 包含平移和旋转
uniform mat4 projection;
uniform mat4 view;

out vec3 v_color;
out vec2 v_texture;

void main()
{
    gl_Position = projection * view * model * vec4(a_position, 1.0);
    v_color = a_color;
    v_texture = a_texture;
}
"""

fragment_src = """
# version 330

in vec3 v_color;
in vec2 v_texture;

uniform sampler2D s_texture;

out vec4 out_color;

void main()
{
    out_color = texture(s_texture, v_texture) * vec4(v_color, 1.0);
}
"""


def glfw_test_github():
    if not glfw.init():
        raise Exception('glfw can not be initialized!')

    window = glfw.create_window(800, 600, "Hello World", None, None)
    if not window:
        glfw.terminate()
        raise Exception('glfw windows can not be created!')

    glfw.set_window_pos(window, 2480, 240)
    glfw.set_window_size_callback(window, window_resize)
    glfw.make_context_current(window)

    glClearColor(0.3, 0.5, 0.5, 1)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    vertices = [-0.5, -0.5, 0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
                0.5, -0.5, 0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
                -0.5, 0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

                -0.5, -0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
                0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
                0.5, 0.5, -0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
                -0.5, 0.5, -0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

                0.5, -0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
                0.5, 0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
                0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
                0.5, -0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

                -0.5, 0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
                -0.5, -0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
                -0.5, 0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

                -0.5, -0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
                0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
                0.5, -0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
                -0.5, -0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

                0.5, 0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
                -0.5, 0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
                -0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
                0.5, 0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0]

    indices = [0, 1, 2, 2, 3, 0,
               4, 5, 6, 6, 7, 4,
               8, 9, 10, 10, 11, 8,
               12, 13, 14, 14, 15, 12,
               16, 17, 18, 18, 19, 16,
               20, 21, 22, 22, 23, 20]

    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER), compileShader(fragment_src, GL_FRAGMENT_SHADER))
    glUseProgram(shader)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    r = requests.get('https://cdn.jsdelivr.net/gh/sheng962464/PicGo/img/20210310113410.jpg')
    image = Image.open(BytesIO(r.content))
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    img_data = image.convert('RGB').tobytes()
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image.width, image.height, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * 8, ctypes.c_void_p(0))

    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * 8, ctypes.c_void_p(vertices.itemsize * 3))

    glEnableVertexAttribArray(2)
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, vertices.itemsize * 8, ctypes.c_void_p(vertices.itemsize * 6))

    # model matrix
    scale = pyrr.matrix44.create_from_scale(pyrr.Vector3([200, 200, 200]))
    translation = pyrr.matrix44.create_from_translation(pyrr.Vector3([400, 200, -3]))
    model_loc = glGetUniformLocation(shader, 'model')

    # view matrix
    # 由于摄像机和物体是相对的，因此这里沿X轴平移500距离，可以理解为摄像仪沿x轴平移-500距离
    # 所以到这里会发现，一切的平移变换都可以认为是对模型做变换
    # 而摄像机是不动的
    view_loc = glGetUniformLocation(shader, 'view')
    view = pyrr.matrix44.create_from_translation(pyrr.Vector3([200, 0, 0]))
    glUniformMatrix4fv(view_loc, 1, GL_FALSE, view)

    # projection matrix
    projection = pyrr.matrix44.create_orthogonal_projection_matrix(0, 800, 0, 600, -1000, 1000)
    proj_loc = glGetUniformLocation(shader, 'projection')
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, projection)

    while not glfw.window_should_close(window):
        glfw.swap_buffers(window)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        rot_x = pyrr.Matrix44.from_x_rotation(0.5 * glfw.get_time())
        rot_y = pyrr.Matrix44.from_y_rotation(0.5 * glfw.get_time())

        rotation = pyrr.matrix44.multiply(rot_x, rot_y)
        model = pyrr.matrix44.multiply(scale, rotation)
        model = pyrr.matrix44.multiply(model, translation)

        glUniformMatrix4fv(model_loc, 1, GL_FALSE, model)

        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)
        glfw.poll_events()

    glfw.terminate()


if __name__ == "__main__":
    glfw_test_github()
