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

<div class="container">
    {#each notificationArray as notification}
        <div class="notification {notification?.type}">
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
        animation: fadeIn 0.7s;
        opacity: 1;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
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