import pygame
import math

WIDTH, HEIGHT = 900, 600

class DialogueManager:
    def __init__(self, font, title_font, text_color='black', border_color='white') -> None:
        self.queued_text = []
        self.text_color = text_color
        self.border_color = border_color
        self.font = font
        self.title_font = title_font

    def calculate_bounds(self):
        return max([self.font.render(self.remove_tags(x), True, 'black').get_width() for x in self.queued_text[0]]), 45 + 25 * (len(self.queued_text[0]) - 1)

    def on_confirm(self):
        if len(self.queued_text):
            self.queued_text.pop(0)

    def queue_text(self, text):
        self.queued_text.append(text)

    def has_dialogue(self):
        return bool(len(self.queued_text))

    def remove_tags(self, text):
        final = ""
        drawing = True
        for char in text:
            if char == "<":
                drawing = False
                continue
            elif char == ">":
                drawing = True
                continue
                
            if drawing:
                final += char
            
        return final

    def draw_tagged_line(self, win, x, y, line, font, base_color='black'):
        fline = ""

        color = base_color

        drawing = True
        cx = x
        for char in line:
            if char == "<":
                drawing = False
                color = ""
                continue
            elif char == ">":
                drawing = True
                if '/' in color:
                    color = base_color
                continue

            if drawing:
                win.blit(t := font.render(char, True, color), (cx, y))
                fline += char
                cx += t.get_width()
            else:
                color += char

    def draw(self, win):
        if self.has_dialogue():
            w, h = self.calculate_bounds()
            w += 30
            h += 15

            x, y = WIDTH // 2 - w // 2, HEIGHT * 0.75 - h // 2
            
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, 128), (0, 0, w, h), 0, 8)
            t = 3 + math.sin(pygame.time.get_ticks() / 300) * 2
            win.blit(s, (x, y))

            pygame.draw.rect(win, '#404040', (x - t, y - t, w, h), 0, 8)
            pygame.draw.rect(win, self.border_color, (x - t, y - t, w, h), 2, 8)

            self.draw_tagged_line(win, x + 5 - t, y + 5 - t, self.queued_text[0][0], self.title_font, self.text_color)

            for i, line in enumerate(self.queued_text[0][1:]):
                self.draw_tagged_line(win, x + 5 - t, y + 45 + 25 * i - t, line, self.font, self.text_color)