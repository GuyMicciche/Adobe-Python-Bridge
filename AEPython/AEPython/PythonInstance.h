#pragma once
#include <string>
#include <AE_GeneralPlug.h>

namespace AEPython
{
	__declspec(dllexport) void init(AEGP_PluginID _my_id, SPBasicSuite* _sP);
	__declspec(dllexport) void exec(const std::string& utf8_code);
	__declspec(dllexport) void showWindow();
	__declspec(dllexport) void showScriptLibrary();  // ADD THIS LINE

	// ADD THESE
	__declspec(dllexport) void togglePythonWindow();
	__declspec(dllexport) void toggleScriptLibrary();
	__declspec(dllexport) bool isPythonWindowVisible();
	__declspec(dllexport) bool isScriptLibraryVisible();
}