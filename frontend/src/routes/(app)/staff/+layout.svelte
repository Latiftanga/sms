<script lang="ts">
  import { auth } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  $: {
    const u = $auth.user;
    if (u && u.system_role !== "SUPERADMIN" && u.permissions?.view_staff !== true) {
      goto("/dashboard");
    }
  }
</script>

<slot />
