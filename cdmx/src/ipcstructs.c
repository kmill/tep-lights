#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

#include <sys/types.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/sem.h>
#include <signal.h>
#include <errno.h>

#include <string.h>

#include "dmx.h"
#include "ipcstructs.h"

RGBPixel * colorlayer_getpixel(ColorLayer * layer, int x, int y)
{
    if (x >= layer->width || y >= layer->height) {
        fprintf(stderr, "Invalid pixel called [%d x %d]: (%d, %d)\n",
                layer->width, layer->height, x, y);
        return NULL;
    }
    int i = x * layer->height + y;
    return &layer->pixels[i];
}

void rgbpixel_print(RGBPixel * pixel)
{
    if (pixel->red > 0.001 || pixel->green > 0.001 || pixel->blue > 0.001) {
        printf("RGBPixel[%0.4f,%0.4f,%0.4f]\n",
               pixel->red,
               pixel->green,
           pixel->blue);
    }
}

RGBPixel * rgbpixel_sethbsvalue(RGBPixel * led, float hue, float brightness, float saturation, float alpha)
/* Great "hsv" algorithm from kmill... */
{
    hue *= 6;
    float angle = ((int)hue % 6) + (hue - (int)hue);

    brightness = MIN(MAX(brightness, 0), 1);
    saturation = MIN(MAX(saturation, 0), 1);

    if (angle < 2) {
        led->red = 1;
        if (angle < 1) {
            led->green = 0;
            led->blue = 1 - angle;
        }
        else {
            led->green = angle - 1;
            led->blue = 0;
        }
    }
    if (angle >= 2 && angle < 4) {
        led->green = 1;
        if (angle < 3) {
            led->red = 3 - angle;
            led->blue = 0;
        }
        else {
            led->red = 0;
            led->blue = angle - 3;
        }
    }
    if (angle >= 4) {
        led->blue = 1;
        if (angle < 5) {
            led->green = 5 - angle;
            led->red = 0;
        }
        else {
            led->green = 0;
            led->red = angle - 5;
        }
    }

    led->red = brightness * (MIN(MAX(brightness - saturation, 0.0), 1.0) *
                             led->red + saturation);
    led->green = brightness * (MIN(MAX(brightness - saturation, 0.0), 1.0) *
                             led->green + saturation);
    led->blue = brightness * (MIN(MAX(brightness - saturation, 0.0), 1.0) *
                             led->blue + saturation);
    led->alpha = alpha;
    return led;
}

void colorlayer_setall(ColorLayer * layer, float red, float green, float blue, float alpha)
{
    int i;

    if (!red && !green && !blue && !alpha) {
        memset(layer->pixels, 0, sizeof(layer->pixels));
        return;
    }

    for (i = 0; i < layer->width * layer->height; i++) {
        rgbpixel_setvalue(&layer->pixels[i], red, green, blue, alpha);
    }
}

RGBPixel * rgbpixel_setvalue(RGBPixel * pixel, float red, float green, float blue, float alpha)
{
    pixel->red = red;
    pixel->green = green;
    pixel->blue = blue;
    pixel->alpha = alpha;
    return pixel;
}

ColorLayer * colorlayer_add(ColorLayer * dst, ColorLayer * src)
{
    int n = dst->width * dst->height;
    int i;
    for (i = 0; i < n; i++) {
        dst->pixels[i].red += src->pixels[i].red;
        dst->pixels[i].green += src->pixels[i].green;
        dst->pixels[i].blue += src->pixels[i].blue;
    }
    return dst;
}

ColorLayer * colorlayer_addalpha(ColorLayer * dst, ColorLayer * src)
{
    int n = dst->width * dst->height;
    float salpha, dalpha;
    int i;
    for (i = 0; i < n; i++) {
        salpha = src->pixels[i].alpha;
        dalpha = dst->pixels[i].alpha;
        dst->pixels[i].red = salpha * src->pixels[i].red + dalpha * dst->pixels[i].red;
        dst->pixels[i].green += salpha * src->pixels[i].green + dst->pixels[i].green * dalpha;
        dst->pixels[i].blue += salpha * src->pixels[i].blue + dalpha * dst->pixels[i].blue;
    }
    return dst;
}

ColorLayer * colorlayer_mult(ColorLayer * dst, ColorLayer * src)
{
    int n = dst->width * dst->height;
    int i;
    for (i = 0; i < n; i++) {
        dst->pixels[i].red *= src->pixels[i].red;
        dst->pixels[i].green *= src->pixels[i].green;
        dst->pixels[i].blue *= src->pixels[i].blue;
    }
    return dst;
}

ColorLayer * colorlayer_copy(ColorLayer * dst, ColorLayer * src) {
    if (dst->width != src->width || dst->height != src->height) {
        fprintf(stderr, "Size mismatch!\n");
        exit(2);
        return NULL;
    }
    memcpy(dst->pixels, src->pixels, sizeof(src->pixels));
    return dst;
}

ColorLayer * colorlayer_superpose(ColorLayer * top, ColorLayer * bottom)
{
    int n = top->width * top->height;
    int i;
    RGBPixel * t, * b;
    for (i = 0; i < n; i++) {
        t = &top->pixels[i];
        b = &bottom->pixels[i];
        t->red = t->red * t->alpha + b->red * (1 - t->alpha);
        t->green = t->green * t->alpha + b->green * (1 - t->alpha);
        t->blue = t->blue * t->alpha + b->blue * (1 - t->alpha);
        t->alpha = MIN(1, t->alpha + b->alpha);
    }
    return top;
}

ColorLayer * colorlayer_create()
{
    ColorLayer * layer = (ColorLayer *)malloc(sizeof(ColorLayer));
    if (!layer) {
        fprintf(stderr, "Could not allocate memory for layer");
        exit(2);
    }
    memset(layer, 0, sizeof(ColorLayer));
    layer->width = PIXELWIDTH;
    layer->height = PIXELHEIGHT;
    return layer;
}


void colorlayer_destroy(ColorLayer * layer)
{
    if (layer) {
        free(layer);
    }
}

int is_client_running(ClientInfo * info)
{
    if (!info || !info->pid) {
        return 0;
    }

    if (kill(info->pid, 0) < 0) {
        return 0;
    }
    return 1;
}

int num_clients(IPCData * data)
{
    int i;
    int total = 0;
    for (i = 0; i < MAXPLUGINS; i++) {
        if (data->plugins[i].id) {
            if (!is_client_running(&data->plugins[i])) {
                data->plugins[i].id = 0;
            }
            else {
                total ++;
            }
        }
    }
    return total;
}

int begin_lightread(ClientInfo * client)
{
    struct sembuf buffer;
    buffer.sem_num = 0;
    buffer.sem_op = 1;
    semop(client->semid, &buffer, 1);
    return 0;
}

int end_lightread(ClientInfo * client)
{
    struct sembuf buffer;
    buffer.sem_num = 0;
    buffer.sem_op = -1;
    semop(client->semid, &buffer, 1);
    return 0;
}

ColorLayer * plugin_useotherlayer(IPCData * data, int id)
{
    begin_lightread(&data->plugins[id]);
    return &data->plugins[id].layer;
}

void plugin_disuseotherlayer(IPCData * data, int id)
{
    end_lightread(&data->plugins[id]);
}

void colorlayer_pushtocollection(DMXPanelCollection * cltn, ColorLayer * layer)
{
    int r, c;
    RGBPixel * pixel;
    for (r = 0; r < layer->height; r++) {
        for (c = 0; c < layer->width; c++) {
            pixel = colorlayer_getpixel(layer, c, r);
            pixel_setrgb(
                         dmxpanelcltn_getpixel(cltn,
                                               r,
                                               c),
                         pixel->red * pixel->alpha,
                         pixel->green * pixel->alpha,
                         pixel->blue * pixel->alpha
                         );
        }
    }
}
