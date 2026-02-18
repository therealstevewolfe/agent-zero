import asyncio
from python.helpers.tool import Tool, Response
import shlex

class OpenClawTool(Tool):
    async def execute(self, **kwargs):
        command = self.args.get("command", "").strip()
        if not command:
             return Response(message="Error: No command provided", break_loop=False)

        # The tool expects arguments for openclaw, e.g., "message send --target me ..."
        full_command = f"openclaw {command}"
        
        try:
            args = shlex.split(full_command)
            
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            output = stdout.decode().strip()
            if stderr:
                output += f"\nStderr: {stderr.decode().strip()}"
                
            return Response(message=output, break_loop=False)
        except Exception as e:
            return Response(message=f"Error executing openclaw command: {str(e)}", break_loop=False)
