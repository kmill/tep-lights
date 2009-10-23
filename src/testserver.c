#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "ipcstructs.h"
#include "server.h"
#include "dmx.h"


int main(int argc, char ** argv)
{
    ServerInfo * info = new_serverenvironment();
    int numc = -1, newc;
    ColorLayer * layer;
    int i;
    int found = 0;
    while (1) {
        found = 0;
        newc = num_clients(info->ipcdata);
        if (newc != numc) {
            printf("Total clients: %d\n", newc);
            numc = newc;
        }
        for (i = 0; i < MAXPLUGINS; i++) {
            if (is_client_running(&info->ipcdata->plugins[i])) {
                found = 1;
                break;
            }
        }

        if (found) {
            layer = plugin_useotherlayer(&info->ipcdata, i);
            colorlayer_pushtocollection(info->panel, layer);
            plugin_disuseotherlayer(&info->ipcdata, i);
        }

        dmxpanelcltn_sendframe(info->panel);
    }

    destroy_serverenvironment(info);
    return 0;
}

