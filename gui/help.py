import moderngl
import freetype
import numpy as np
from pyrr import Matrix44

class TextRenderer:
    def __init__(self, ctx):
        self.ctx = ctx

        # Load font with FreeType
        try:
            self.face = freetype.Face("./fonts/Roboto-Regular.ttf")
            self.face.set_char_size(16 * 64)  # font size
        except freetype.ft_errors.FT_Exception as e:
            print(f"Font loading error: {e}")
            self.face = None

        # Enable blending for transparency
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)

        # Define shaders
        vertex_shader = """
        #version 330 core
        in vec2 in_position;
        in vec2 in_texcoord;
        out vec2 v_texcoord;
        uniform mat4 projection;
        void main() {
            gl_Position = projection * vec4(in_position, 0.0, 1.0);
            v_texcoord = in_texcoord;
        }
        """

        fragment_shader = """
        #version 330 core
        in vec2 v_texcoord;
        out vec4 fragColor;
        uniform sampler2D text_texture;
        uniform vec3 textColor;
        void main() {
            float alpha = texture(text_texture, v_texcoord).r;
            fragColor = vec4(textColor, alpha);  // Use textColor with alpha from red channel
        }
        """

        # Initialize shader program
        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )

        self.characters = self._load_characters()

        # Initialize vertex buffer and vertex array
        self.vertex_buffer = self.ctx.buffer(reserve=4 * 6 * 4)
        self.quad_vao = self.ctx.vertex_array(
            self.program,
            [(self.vertex_buffer, "2f 2f", "in_position", "in_texcoord")]
        )

    def _load_characters(self):
        characters = {}
        for char_code in range(128):
            self.face.load_char(chr(char_code))
            bitmap = self.face.glyph.bitmap
            width, height = bitmap.width, bitmap.rows

            # Create texture and swizzle
            texture = self.ctx.texture((width, height), 1, bytes(bitmap.buffer), dtype='f1')
            texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            texture.swizzle = 'RRRR'  # Map red channel to RGB for grayscale font

            characters[chr(char_code)] = Character(
                texture, (width, height),
                (self.face.glyph.bitmap_left, self.face.glyph.bitmap_top),
                self.face.glyph.advance.x
            )
        return characters

    def render_text(self, text, x, y, scale, color=(1.0, 1.0, 1.0)):
        self.program['textColor'].value = color  # Set color if used in fragment shader
        self.program['text_texture'].value = 0

        projection = Matrix44.orthogonal_projection(0, self.ctx.screen.width, 0, self.ctx.screen.height, -1, 1)
        self.program['projection'].write(projection.astype('f4').tobytes())

        for char in text:
            ch = self.characters[char]
            xpos = x + ch.bearing[0] * scale
            ypos = y - (ch.size[1] - ch.bearing[1]) * scale
            w = ch.size[0] * scale
            h = ch.size[1] * scale

            vertices = np.array([
                xpos, ypos + h, 0.0, 0.0,
                xpos, ypos, 0.0, 1.0,
                xpos + w, ypos, 1.0, 1.0,
                xpos, ypos + h, 0.0, 0.0,
                xpos + w, ypos, 1.0, 1.0,
                xpos + w, ypos + h, 1.0, 0.0
            ], dtype='f4')

            self.vertex_buffer.write(vertices.tobytes())
            ch.texture_id.use(location=0)  # Ensure texture is bound correctly
            self.quad_vao.render(moderngl.TRIANGLES)

            # Advance cursor for next glyph
            x += (ch.advance >> 6) * scale

class Character:
    def __init__(self, texture_id, size, bearing, advance):
        self.texture_id = texture_id
        self.size = size
        self.bearing = bearing
        self.advance = advance
