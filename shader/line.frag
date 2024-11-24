#version 330 core

uniform vec3 color;  // Define color uniform to control line color

out vec4 fragColor;

void main() {
    fragColor = vec4(color, 1.0);  // Use the color uniform for fragment color
}
