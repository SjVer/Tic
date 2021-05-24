using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;

namespace AttemptLang
{
	class Program
	{
		static AssemblyName an;
		static AssemblyBuilder ab;
		static ModuleBuilder mb;
		static TypeBuilder tb;
		static _AppDomain ad;
		static MethodBuilder meb;
		static ILGenerator il;
		
		static void Main(string[] args)
		{
			ad = AppDomain.CurrentDomain;
			an = new AssemblyName("lol");
			ab = ad.DefineDynamicAssembly(an, AssemblyBuilderAccess.Save);
			mb = ab.DefineDynamicModule("Lol", "idk.exe");
			meb = tb.DefineMethod("main", MethodAttributes.Public | MethodAttributes.Static);
			il = meb.GetILGenerator();
			an.Name = "MyApp";
			ab.SetEntryPoint(meb);
			
			StreamReader sr = new StreamReader(args[0]);
			string Code = sr.ReadToEnd();

			//The codes below is the creation of our own syntax in its own command.
			foreach (string cmd in Code.Split('\n'))
			{
			  if (cmd.StartsWith("print"))
			  {
				  il.Emit(OpCodes.Ldstr, cmd.Substring(6));
				  il.Emit(OpCodes.Call, typeof(System.Console).GetMethod("Write", new System.Type[] { typeof(string) }));
			  }
			  if (cmd.StartsWith("println"))
			  {
				  il.Emit(OpCodes.Ldstr, cmd.Substring(8));
				  il.Emit(OpCodes.Call, typeof(System.Console).GetMethod("WriteLine", new System.Type[] { typeof(string) }));
				  {
				  
				  }
			  }
			  il.Emit(OpCodes.Ret);
			  tb.CreateType();
			  ab.Save(Path.GetFileNameWithoutExtension(args[0]) + ".exe");
			}
		}
	}
}