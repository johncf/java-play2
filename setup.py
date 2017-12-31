from cx_Freeze import setup, Executable

options = {
    "build_exe": {
        "includes": ["asyncio.compat",
                     "asyncio.base_futures",
                     "asyncio.base_tasks",
                     "asyncio.base_subprocess",
                     "asyncio.proactor_events",
                     "asyncio.constants",
                     "asyncio.sslproto",
                     "asyncio.selector_events",
                     "asyncio.windows_utils",
                     "engineio.async_threading"],
        "excludes": ["gevent"],
        "include_files": ["static", "jdk.path", "LICENSE"]
    }
}

setup(
    name = "Java Play",
    version = "1.1",
    description = "A web-based Java Playground",
    executables = [Executable("server.py")],
    options = options)
