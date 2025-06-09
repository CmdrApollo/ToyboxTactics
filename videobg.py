import pygame

pygame.init()

FONT = pygame.font.Font("assets/visual/nunito.ttf", 72)
SMALLFONT = pygame.font.Font("assets/visual/nunito.ttf", 50)

WIDTH, HEIGHT = 1280, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT))

def hsv_to_rgb(h, s, v):
    if s == 0.0:
        r = g = b = int(v * 255)
        return r, g, b

    h = h % 360  # wrap hue
    h_sector = h / 60
    i = int(h_sector)
    f = h_sector - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    elif i == 5:
        r, g, b = v, p, q

    return int(r * 255), int(g * 255), int(b * 255)

def darken(c, v=0.1):
    col = pygame.Color(c)
    t = 1 - v
    return (col.r * t, col.g * t, col.b * t)

def main():
    clock = pygame.time.Clock()

    d = 120

    run = True
    while run:
        delta = clock.tick(60) / 1000

        # d += delta * 5
        # if d > 360:
        #     d -= 360

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
    
        c = hsv_to_rgb(d, 0.5, 1.0)
        c2 = darken(c)

        WIN.fill(c)

        t = 0

        for x in range(WIDTH // 40 + 1):
            for y in range(HEIGHT // 40 + 1):
                if (x + y) & 1:
                    pygame.draw.rect(WIN, c2, (x * 40 - t, y * 40 - t, 40, 40))

        WIN.blit(s := FONT.render("Adding a Tutorial to my Indie Game", True, 'black'), (3 + WIDTH // 2 - s.get_width() // 2, 28))
        WIN.blit(s := FONT.render("Adding a Tutorial to my Indie Game", True, 'white'), (WIDTH // 2 - s.get_width() // 2, 25))
        WIN.blit(s := SMALLFONT.render("Toybox Tactics Devlog #2", True, 'black'), (WIDTH // 2 - s.get_width() // 2 + 2, 482))
        WIN.blit(s := SMALLFONT.render("Toybox Tactics Devlog #2", True, 'white'), (WIDTH // 2 - s.get_width() // 2, 480))

        pygame.display.flip()
    
    pygame.quit()

main()