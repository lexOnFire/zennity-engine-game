from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtOpenGL import QOpenGLShaderProgram, QOpenGLShader
from PySide6.QtGui import QOpenGLFunctions
from PySide6.QtCore import QTimer
import time

VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec2 position;
layout(location = 1) in vec2 uv;

out vec2 v_uv;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    v_uv = uv;
}
"""

DEFAULT_FRAGMENT_SHADER = """#version 330 core
in vec2 v_uv;
out vec4 fragColor;

void main() {
    fragColor = vec4(1.0, 0.0, 1.0, 1.0); // Default error/fallback color (magenta)
}
"""

class MaterialPreviewWidget(QOpenGLWidget, QOpenGLFunctions):
    """
    Widget de preview OpenGL para Materiais.
    Renderiza um Quad em tela cheia com o Fragment Shader gerado pelo MaterialGraph.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.program = None
        
        self.current_fragment_shader = DEFAULT_FRAGMENT_SHADER
        self.uniforms_decl = {}
        
        self.start_time = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS

    def initializeGL(self):
        self.initializeOpenGLFunctions()
        self.glClearColor(0.1, 0.1, 0.15, 1.0)

        # Quad data (x, y, u, v)
        quad_vertices = [
            -1.0, -1.0,  0.0, 0.0,
             1.0, -1.0,  1.0, 0.0,
            -1.0,  1.0,  0.0, 1.0,
             1.0,  1.0,  1.0, 1.0,
        ]
        
        import numpy as np
        vertex_data = np.array(quad_vertices, dtype=np.float32)

        # In Qt, we can just use the shader program to enable attributes without explicit VAO/VBOs for a simple quad
        # but to be safe and cross-platform, we should use QOpenGLBuffer and QOpenGLVertexArrayObject
        # Or simpler: just use vertexAttribPointer when binding the program during paintGL
        self.vertex_data = vertex_data

        self._compile_shader()

    def set_shader(self, fragment_code: str, uniforms: dict):
        """Atualiza o fragment shader e re-compila."""
        self.current_fragment_shader = fragment_code
        self.uniforms_decl = uniforms
        if self.context():
            self.makeCurrent()
            self._compile_shader()
            self.update()

    def _compile_shader(self):
        if self.program:
            self.program.removeAllShaders()
            self.program.deleteLater()
            self.program = None
            
        self.program = QOpenGLShaderProgram(self)
        
        if not self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_SHADER):
            print("Erro ao compilar Vertex Shader:", self.program.log())
            return
            
        if not self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, self.current_fragment_shader):
            print("Erro ao compilar Fragment Shader:", self.program.log())
            self.program.removeAllShaders()
            self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, VERTEX_SHADER)
            self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, DEFAULT_FRAGMENT_SHADER)
            
        self.program.link()

    def resizeGL(self, w: int, h: int):
        self.glViewport(0, 0, w, h)

    def paintGL(self):
        self.glClear(self.GL_COLOR_BUFFER_BIT | self.GL_DEPTH_BUFFER_BIT)

        if not self.program or not self.program.isLinked():
            return

        self.program.bind()

        self.program.enableAttributeArray(0)
        self.program.enableAttributeArray(1)
        
        # Position (2 floats) starts at offset 0, stride 16 bytes
        self.program.setAttributeArray(0, self.GL_FLOAT, self.vertex_data, 2, 16)
        
        # UV (2 floats) starts at offset 8 (2 floats), stride 16 bytes
        # Using memoryview slice to offset the pointer
        uv_data = memoryview(self.vertex_data.tobytes())[8:]
        self.program.setAttributeArray(1, self.GL_FLOAT, uv_data, 2, 16)

        self.glDrawArrays(self.GL_TRIANGLE_STRIP, 0, 4)

        self.program.disableAttributeArray(0)
        self.program.disableAttributeArray(1)

        self.program.release()

