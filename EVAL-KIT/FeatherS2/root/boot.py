import storage

storage.remount("/", False, disable_concurrent_write_protection=True)
