<script lang="ts">
    import { notifications } from "../stores";
    import type { NotificationInfo } from "../stores";

    let activeNotifications = {};
    let currentNotification = 0;

    $: notificationArray = Object.values<NotificationInfo>(activeNotifications);

    notifications.subscribe(notification => {
        if (notification) {
            const id = currentNotification++;
            activeNotifications[id] = notification;

            setTimeout(() => {
                delete activeNotifications[id];
                activeNotifications = activeNotifications;
                currentNotification--;
            }, 2500);
        }
    });
</script>

{#each notificationArray as notification}
    <div class="notification {notification?.type}">
        <h2>{notification?.data}</h2>
    </div>
{/each}

<style>
    .notification {

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