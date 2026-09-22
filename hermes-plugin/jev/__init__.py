from . import schemas, tools


def register(ctx):
    ctx.register_tool(
        name="jev_ask",
        toolset="jev",
        schema=schemas.JEV_ASK,
        handler=tools.jev_ask,
    )
