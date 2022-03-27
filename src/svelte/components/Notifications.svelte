<script lang="ts">
    import { notifications } from "../stores";
    import type { NotificationInfo } from "../stores";

    let activeNotifications: Notification = {};
    $: notificationArray = Object.entries(activeNotifications);

    notifications.subscribe(notification => {
        if (notification) {
            const id = crypto.randomUUID();
            activeNotifications[id] = notification;

            setTimeout(() => {
                setTimeout(() => {
                    delete activeNotifications[id];
                    activeNotifications = activeNotifications;
                }, 500);

                document.getElementById(id).classList.add("hide");
            }, 2500);
        }
    });

    type Notification = {
        [key: string]: NotificationInfo;
    };
</script>

<div class="container">
    {#each notificationArray as [id, notification]}
        <div id="{id}" class="notification {notification?.type}">
            {notification?.data}
        </div>
    {/each}
</div>

<style>
    .container {
        position: fixed;
        display: flex;
        flex-direction: column;
        bottom: 60px;
        gap: 5px;
        left: 5px;
        user-select: none;
    }

    .notification {
        border-radius: 5px;
        color: white;
        padding: 5px;
        font-size: 1.2em;
        animation: slideIn 0.7s;
    }

    .hide {
        visibility: hidden;
        opacity: 0;
        transition: visibility 0s 0.5s, opacity 0.5s linear;
    }

    @keyframes slideIn {
        0% {
            transform: translateX(-500px);
        }

        85% {
            transform: translateX(8px);
        }

        100% {
            transform: translateX(0);
        }
    }

    .success {
        background-color: #76ec6c;
    }

    .info {
        background-color: #387fe9;
    }

    .error {
        background-color: #dd5656;
    }
</style>