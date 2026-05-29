<script lang="ts">
  import { auth } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  $: {
    const u = $auth.user;
    if (u && u.system_role !== "SUPERADMIN") {
      const p = u.permissions ?? {};
      if (!p.manage_school_config && !p.manage_academic_structure && !p.manage_users) {
        goto("/dashboard");
      }
    }
  }
</script>

<slot />
