from keystone_cli import main


def test_main_prints_core_greeting(capsys):
    main()
    assert capsys.readouterr().out == "Hello from keystone!\n"
