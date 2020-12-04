import ast
import asyncio
import collections
import traceback

import discord
import import_expression
import typing
from discord.ext import commands
from jishaku.repl import Scope


class KeywordTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        # Do not affect nested function definitions
        return node

    def visit_AsyncFunctionDef(self, node):
        # Do not affect nested async function definitions
        return node

    def visit_ClassDef(self, node):
        # Do not affect nested class definitions
        return node

    def visit_Return(self, node):
        # Do not modify valueless returns
        if node.value is None:
            return node

        # Otherwise, replace the return with a yield & valueless return
        return ast.If(
            test=ast.NameConstant(
                value=True,  # if True; aka unconditional, will be optimized out
                lineno=node.lineno,
                col_offset=node.col_offset
            ),
            body=[
                # yield the value to be returned
                ast.Expr(
                    value=ast.Yield(
                        value=node.value,
                        lineno=node.lineno,
                        col_offset=node.col_offset
                    ),
                    lineno=node.lineno,
                    col_offset=node.col_offset
                ),
                # return valuelessly
                ast.Return(
                    value=None,
                    lineno=node.lineno,
                    col_offset=node.col_offset
                )
            ],
            orelse=[],
            lineno=node.lineno,
            col_offset=node.col_offset
        )


class AsyncCodeExecutor:

    __slots__ = ('args', 'arg_names', 'code', 'loop', 'scope')

    def __init__(self, code: str, scope: Scope = None, arg_dict: dict = None, loop: asyncio.BaseEventLoop = None):
        self.args = [self]
        self.arg_names = ['_async_executor']

        for key, value in arg_dict.items():
            self.arg_names.append(key)
            self.args.append(value)

        self.code = wrap_code(code, args=', '.join(self.arg_names))
        self.scope = scope
        self.loop = loop

    def __aiter__(self):
        exec(compile(self.code, '<repl>', 'exec'), self.scope.globals, self.scope.locals)  # pylint: disable=exec-used
        return self.scope.locals.get('_repl_coroutine')


async def send_traceback(destination: discord.abc.Messageable, verbosity: int, *exc_info):
    etype, value, trace = exc_info

    traceback_content = "".join(traceback.format_exception(etype, value, trace, verbosity)).replace("``", "`\u200b`")

    embed = discord.Embed(title="", description=f"```{traceback_content}```")

    return await destination.send(embed=embed)


class ReplResponseReactor:  # pylint: disable=too-few-public-methods
    def __init__(self, message: discord.Message, loop: typing.Optional[asyncio.BaseEventLoop] = None):
        self.message = message
        self.loop = loop
        self.handle = None
        self.raised = False

    async def __aiter__(self, exc_type, exc_val, exc_tb):

        # nothing went wrong, who cares lol
        if not exc_val:
            return

        await send_traceback(
            self.message.channel,
            1, exc_type, exc_val, exc_tb
        )

        return True  # the exception has been handled


CORO_CODE = """
 async def _repl_coroutine():
     import asyncio
     import aiohttp
     import discord
     from discord.ext import commands

     try:
         pass
     finally:
         _async_executor.scope.globals.update(locals())
 """.format(import_expression.constants.IMPORTER)


def wrap_code(code: str, args: str = '') -> ast:
    user_code = import_expression.parse(code, mode='exec')
    mod = import_expression.parse(CORO_CODE.format(args), mode='exec')

    definition = mod.body[-1]  # async def ...:
    assert isinstance(definition, ast.AsyncFunctionDef)

    try_block = definition.body[-1]  # try:
    assert isinstance(try_block, ast.Try)

    try_block.body.extend(user_code.body)

    ast.fix_missing_locations(mod)

    KeywordTransformer().generic_visit(try_block)

    last_expr = try_block.body[-1]

    # if the last part isn't an expression, ignore it
    if not isinstance(last_expr, ast.Expr):
        return mod

    # if the last expression is not a yield
    if not isinstance(last_expr.value, ast.Yield):
        # copy the value of the expression into a yield
        yield_stmt = ast.Yield(last_expr.value)
        ast.copy_location(yield_stmt, last_expr)
        # place the yield into its own expression
        yield_expr = ast.Expr(yield_stmt)
        ast.copy_location(yield_expr, last_expr)

        # place the yield where the original expression was
        try_block.body[-1] = yield_expr

    return mod


def codeblock_converter(argument):
    Codeblock = collections.namedtuple('Codeblock', 'language content')

    if not argument.startswith('`'):
        return Codeblock(None, argument)
    last = collections.deque(maxlen=3)
    backticks = 0
    in_language = False
    in_code = False
    language = []
    code = []

    for char in argument:
        if char == '`' and not in_code and not in_language:
            backticks += 1  # to help keep track of closing backticks
        if last and last[-1] == '`' and char != '`' or in_code and ''.join(last) != '`' * backticks:
            in_code = True
            code.append(char)
        if char == '\n':  # \n delimits language and code
            in_language = False
            in_code = True
        # we're not seeing a newline yet but we also passed the opening ```
        elif ''.join(last) == '`' * 3 and char != '`':
            in_language = True
            language.append(char)
        elif in_language:  # we're in the language after the first non-backtick character
            if char != '\n':
                language.append(char)

        last.append(char)

    if not code and not language:
        code[:] = last

    return Codeblock(''.join(language), ''.join(code[len(language):-backticks]))


def code_limiter(argument):
    """no more than...
    5 functions
    10 iters per loop
    1400 code characters
    12 variables
    8 built in functions
    and no imports
    """
    # disable imports somehow here


def get_var_dict(ctx: commands.Context, prefix: str = '_'):
    raw_var_dict = {
        'author': ctx.author,
        'bot': ctx.bot,
        'channel': ctx.channel,
        'ctx': ctx,
        'find': discord.utils.find,
        'get': discord.utils.get,
        'guild': ctx.guild,
        'message': ctx.message
    }

    return {f'{prefix}{k}': v for k, v in raw_var_dict.items()}


def get_event_args(prefix: str = '&'):
    allowed_events = {
        'on_typing': [1, 2, 3],
        'on_message': [1],
        'on_message_delete': [1],
        'on_bulk_message_delete': [1],
        'on_message_edit': [1, 2],
        'on_reaction_add': [1, 2],
        'on_reaction_remove': [1, 2],
        'on_reaction_clear': [1, 2],
        'on_guild_channel_delete': [1],
        'on_guild_channel_create': [1],
        'on_guild_channel_update': [1, 2],
        'on_guild_channel_pins_update': [1, 2],
        'on_guild_integrations_update': [1, 2],
        'on_webhooks_update': [1],
        'on_member_join': [1],
        'on_member_remove': [1],
        'on_member_update': [1, 2],
        'on_guild_update': [1, 2],
        'on_guild_role_create': [1],
        'on_guild_role_delete': [1],
        'on_guild_role_update': [1, 2],
        'on_voice_state_update': [1, 2, 3],
        'on_member_ban': [1, 2],
        'on_member_unban': [1, 2],
        'on_invite_create': [1],
        'on_invite_delete': [1]
    }

    return {k: f'{prefix}{v}' for k, v in allowed_events.items()}
