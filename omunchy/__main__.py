from omunchy.update import maybe_update_and_reexec

if __name__ == "__main__":
    maybe_update_and_reexec(splash=True)
    from omunchy.app import main

    main()
