from discord import Embed, Color

async def checkIfAuthorIsMe(ctx):
    if ctx.author.id != 382302674164514818:
        embed = Embed(
            title="You are not authorized.",
            description="You can't do this command !",
            color=Color.red(),
        )
        await ctx.send(embed=embed)
        return False

    return True