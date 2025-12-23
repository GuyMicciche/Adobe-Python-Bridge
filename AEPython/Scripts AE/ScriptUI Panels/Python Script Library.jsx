/*
AEPython Script Library - ScriptUI Version
Dockable panel for managing and executing Python scripts in After Effects

Usage:
    // Python Qt Version (commented out)
    // Python.exec("import script_library; script_library.ShowScriptLibrary()");
    
    // ScriptUI Version
    #include "AEPython_ScriptLibrary_UI.jsx"
    AEPythonScriptLibrary.showPanel();
*/

if(typeof JSON!=='object'){JSON={};}(function(){'use strict';function f(n){return n<10?'0'+n:n;}function this_value(){return this.valueOf();}if(typeof Date.prototype.toJSON!=='function'){Date.prototype.toJSON=function(){return isFinite(this.valueOf())?this.getUTCFullYear()+'-'+f(this.getUTCMonth()+1)+'-'+f(this.getUTCDate())+'T'+f(this.getUTCHours())+':'+f(this.getUTCMinutes())+':'+f(this.getUTCSeconds())+'Z':null;};Boolean.prototype.toJSON=this_value;Number.prototype.toJSON=this_value;String.prototype.toJSON=this_value;}var cx,escapable,gap,indent,meta,rep;function quote(string){escapable.lastIndex=0;return escapable.test(string)?'"'+string.replace(escapable,function(a){var c=meta[a];return typeof c==='string'?c:'\\u'+('0000'+a.charCodeAt(0).toString(16)).slice(-4);})+'"':'"'+string+'"';}function str(key,holder){var i,k,v,length,mind=gap,partial,value=holder[key];if(value&&typeof value==='object'&&typeof value.toJSON==='function'){value=value.toJSON(key);}if(typeof rep==='function'){value=rep.call(holder,key,value);}switch(typeof value){case'string':return quote(value);case'number':return isFinite(value)?String(value):'null';case'boolean':case'null':return String(value);case'object':if(!value){return'null';}gap+=indent;partial=[];if(Object.prototype.toString.apply(value)==='[object Array]'){length=value.length;for(i=0;i<length;i+=1){partial[i]=str(i,value)||'null';}v=partial.length===0?'[]':gap?'[\n'+gap+partial.join(',\n'+gap)+'\n'+mind+']':'['+partial.join(',')+']';gap=mind;return v;}if(rep&&typeof rep==='object'){length=rep.length;for(i=0;i<length;i+=1){if(typeof rep[i]==='string'){k=rep[i];v=str(k,value);if(v){partial.push(quote(k)+(gap?': ':':')+v);}}}}else{for(k in value){if(Object.prototype.hasOwnProperty.call(value,k)){v=str(k,value);if(v){partial.push(quote(k)+(gap?': ':':')+v);}}}}v=partial.length===0?'{}':gap?'{\n'+gap+partial.join(',\n'+gap)+'\n'+mind+'}':'{'+partial.join(',')+'}';gap=mind;return v;}}if(typeof JSON.stringify!=='function'){escapable=/[\\\"\u0000-\u001f\u007f-\u009f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g;meta={'\b':'\\b','\t':'\\t','\n':'\\n','\f':'\\f','\r':'\\r','"':'\\"','\\':'\\\\'};JSON.stringify=function(value,replacer,space){var i;gap='';indent='';if(typeof space==='number'){for(i=0;i<space;i+=1){indent+=' ';}}else if(typeof space==='string'){indent=space;}rep=replacer;if(replacer&&typeof replacer!=='function'&&(typeof replacer!=='object'||typeof replacer.length!=='number')){throw new Error('JSON.stringify');}return str('',{'':value});};}if(typeof JSON.parse!=='function'){cx=/[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g;JSON.parse=function(text,reviver){var j;function walk(holder,key){var k,v,value=holder[key];if(value&&typeof value==='object'){for(k in value){if(Object.prototype.hasOwnProperty.call(value,k)){v=walk(value,k);if(v!==undefined){value[k]=v;}else{delete value[k];}}}}return reviver.call(holder,key,value);}text=String(text);cx.lastIndex=0;if(cx.test(text)){text=text.replace(cx,function(a){return'\\u'+('0000'+a.charCodeAt(0).toString(16)).slice(-4);});}if(/^[\],:{}\s]*$/.test(text.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g,'@').replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,']').replace(/(?:^|:|,)(?:\s*\[)+/g,''))){j=eval('('+text+')');return typeof reviver==='function'?walk({'':j},''):j;}throw new SyntaxError('JSON.parse');};}}());

(function(thisObj) {
    
    // =========================================================================
    // GLOBAL OBJECT FOR API ACCESS
    // =========================================================================
    if (!$.global.AEPythonScriptLibrary) {
        $.global.AEPythonScriptLibrary = {};
    }
    var AEPythonScriptLibrary = $.global.AEPythonScriptLibrary;
    
    // =========================================================================
    // CONFIGURATION
    // =========================================================================
    
    var CONFIG = {
        SCRIPTS_ROOT: Folder.myDocuments.fsName + "/AEPython/Scripts",
        METADATA_FILE: Folder.myDocuments.fsName + "/AEPython/script_library.json",
        WINDOW_TITLE: "Python Script Library",
        VERSION: "1.0.0"
    };
    
    // =========================================================================
    // UTILITY FUNCTIONS
    // =========================================================================
    
    function readTextFile(filePath) {
        var file = new File(filePath);
        if (!file.exists) return null;
        
        file.encoding = "UTF-8";
        if (!file.open("r")) return null;
        
        var content = file.read();
        file.close();
        return content;
    }
    
    function writeTextFile(filePath, content) {
        var file = new File(filePath);
        file.encoding = "UTF-8";
        
        if (!file.open("w")) return false;
        
        file.write(content);
        file.close();
        return true;
    }
    
    function ensureFolder(folderPath) {
        var folder = new Folder(folderPath);
        if (!folder.exists) {
            folder.create();
        }
        return folder;
    }
    
    function getRelativePath(fullPath, basePath) {
        var relative = fullPath.replace(basePath, "");
        if (relative.charAt(0) === "/" || relative.charAt(0) === "\\") {
            relative = relative.substring(1);
        }
        return relative.replace(/\\/g, "/");
    }
    
    function formatDate(dateStr) {
        if (!dateStr) return "";
        var d = new Date(dateStr);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString();
    }
    
    // =========================================================================
    // METADATA MANAGER
    // =========================================================================
    
    var MetadataManager = {
        metadata: {},
        
        load: function() {
            var content = readTextFile(CONFIG.METADATA_FILE);
            if (content) {
                try {
                    this.metadata = JSON.parse(content);
                } catch(e) {
                    alert("Failed to parse metadata: " + e.toString());
                    this.metadata = {};
                }
            }
            return this.metadata;
        },
        
        save: function() {
            ensureFolder(Folder.myDocuments.fsName + "/AEPython");
            var json = JSON.stringify(this.metadata, null, 2);
            return writeTextFile(CONFIG.METADATA_FILE, json);
        },
        
        get: function(scriptId) {
            return this.metadata[scriptId] || this.createDefault(scriptId);
        },
        
        createDefault: function(scriptId) {
            var parts = scriptId.split("/");
            var filename = parts[parts.length - 1];
            var category = parts.length > 1 ? parts[parts.length - 2] : "Uncategorized";
            
            return {
                name: filename.replace(".py", ""),
                description: "",
                category: category,
                tags: [],
                favorite: false,
                author: "",
                created: this.formatDate(new Date()),
                modified: this.formatDate(new Date()),
                file_path: ""
            };
        },
        
        update: function(scriptId, updates) {
            if (!this.metadata[scriptId]) {
                this.metadata[scriptId] = this.createDefault(scriptId);
            }
            
            for (var key in updates) {
                this.metadata[scriptId][key] = updates[key];
            }
            
            this.metadata[scriptId].modified = this.formatDate(new Date());  // ✅ GOOD
            this.save();
        },
        
        getCategories: function() {
            var categories = {};
            for (var id in this.metadata) {
                categories[this.metadata[id].category] = true;
            }
            
            var arr = [];
            for (var cat in categories) {
                arr.push(cat);
            }
            return arr.sort();
        },
        
        getAllTags: function() {
            var tags = {};
            for (var id in this.metadata) {
                var scriptTags = this.metadata[id].tags || [];
                for (var i = 0; i < scriptTags.length; i++) {
                    tags[scriptTags[i]] = true;
                }
            }
            
            var arr = [];
            for (var tag in tags) {
                arr.push(tag);
            }
            return arr.sort();
        },
        formatDate: function(date) {
            // ExtendScript-compatible ISO date
            function pad(num) {
                return num < 10 ? '0' + num : num;
            }
            return date.getFullYear() + '-' +
                   pad(date.getMonth() + 1) + '-' +
                   pad(date.getDate()) + 'T' +
                   pad(date.getHours()) + ':' +
                   pad(date.getMinutes()) + ':' +
                   pad(date.getSeconds()) + 'Z';
        } 
    };
    
    // =========================================================================
    // SCRIPT SCANNER
    // =========================================================================
    
    var ScriptScanner = {
        scan: function() {
            var scripts = [];
            var rootFolder = new Folder(CONFIG.SCRIPTS_ROOT);
            
            if (!rootFolder.exists) {
                ensureFolder(CONFIG.SCRIPTS_ROOT);
                return scripts;
            }
            
            this.scanFolder(rootFolder, CONFIG.SCRIPTS_ROOT, scripts);
            
            // Update metadata for found scripts
            var newMetadata = {};
            for (var i = 0; i < scripts.length; i++) {
                var script = scripts[i];
                var existing = MetadataManager.metadata[script.id];
                
                if (existing) {
                    existing.file_path = script.path;
                    existing.category = script.category;
                    newMetadata[script.id] = existing;
                } else {
                    var meta = MetadataManager.createDefault(script.id);
                    meta.file_path = script.path;
                    meta.category = script.category;
                    newMetadata[script.id] = meta;
                }
            }
            
            MetadataManager.metadata = newMetadata;
            MetadataManager.save();
            
            return scripts;
        },
        
        scanFolder: function(folder, basePath, scripts) {
			var files = folder.getFiles();
			
			for (var i = 0; i < files.length; i++) {
				var file = files[i];
				
				if (file instanceof Folder) {
					// ✅ SKIP if folder contains __init__.py (Python module/package)
					var initFile = new File(file.fsName + "/__init__.py");
					if (initFile.exists) {
						continue;  // Skip entire module folder
					}
					
					// Recursively scan non-module folders
					this.scanFolder(file, basePath, scripts);
				} else if (file instanceof File && file.name.match(/\.py$/i)) {
					// Process .py files normally
					var relativePath = file.fsName.substring(basePath.length);
					if (relativePath.charAt(0) === "/" || relativePath.charAt(0) === "\\") {
						relativePath = relativePath.substring(1);
					}
					relativePath = relativePath.replace(/\\/g, "/");
					
					var parts = relativePath.split("/");
					var category = parts.length > 1 ? parts[parts.length - 2] : "Uncategorized";
					
					scripts.push({
						id: relativePath,
						path: file.fsName,
						category: category,
						filename: file.name
					});
				}
			}
		}
    };
    
    // =========================================================================
    // SCRIPT EXECUTOR
    // =========================================================================
    
    var ScriptExecutor = {
		execute: function(scriptId) {
			var meta = MetadataManager.get(scriptId);
		
			if (!new File(meta.file_path).exists) {
				alert("Script file not found:\n" + meta.file_path);
				return;
			}
			
			try {
				// FIXED: Match Python run_script() exactly
				var escapedPath = meta.file_path.replace(/\\/g, '/');
				var pythonCode = [
					'import sys, os',
					'import AEPython as ae',
					'import _AEPython as _ae',
					'',
					'with open(r"' + escapedPath + '", "r", encoding="utf-8") as _f:',
					'    _code = _f.read()',
					'',
					'_exec_namespace = {',
					'    "__name__": "__main__",',
					'    "__builtins__": __builtins__,',
					'    "ae": ae,',
					'    "_ae": _ae',
					'}',
					'if "' + escapedPath + '":',
					'    _exec_namespace["__file__"] = "' + escapedPath + '"',
					'    module_dir = os.path.dirname("' + escapedPath + '")',
					'    sys.path.insert(0, module_dir)',
					'',
					'exec(compile(_code, "' + escapedPath + '", "exec"), _exec_namespace)'
				].join('\n');
				
				Python.exec(pythonCode);
				
			} catch(e) {
				alert("Error executing script:\n" + e.toString());
			}
		}
	};
    
    // =========================================================================
    // UI BUILDER
    // =========================================================================
    
    var UIBuilder = {
        currentScriptId: null,
        allScripts: [],
        filteredScripts: [],
        scriptListItems: [],
        
        buildPanel: function(thisObj) {
            var panel = (thisObj instanceof Panel) ? thisObj : new Window("palette", CONFIG.WINDOW_TITLE, undefined, {resizeable: true});
            
            panel.spacing = 5;
            panel.margins = 10;
            panel.alignChildren = ["fill", "fill"];
            panel.minimumSize = [700, 400];   // Prevent panel from getting too small
            
            // Search and filters
            var searchGroup = panel.add("group");
            searchGroup.orientation = "row";
            searchGroup.alignment = ["fill", "top"];
            searchGroup.alignChildren = ["left", "center"];
            searchGroup.margins = 0;
            searchGroup.spacing = 5;
            
            searchGroup.add("statictext", undefined, "Search:");
            var searchInput = searchGroup.add("edittext", undefined, "");
            searchInput.characters = 25;
            searchInput.alignment = ["fill", "center"];
            
            searchGroup.add("statictext", undefined, "Category:");
            var categoryDropdown = searchGroup.add("dropdownlist", undefined, ["All Categories"]);
            categoryDropdown.selection = 0;
            categoryDropdown.preferredSize.width = 150;
            
            var favButton = searchGroup.add("button", undefined, "\u2605 Favorites");
            favButton.preferredSize.width = 110;
            
            var refreshButton = searchGroup.add("button", undefined, "\u27F3 Refresh");
            refreshButton.preferredSize.width = 80;
            
            // Main content area
            var mainGroup = panel.add("group");
            mainGroup.orientation = "row";
            mainGroup.alignment = ["fill", "fill"];
            mainGroup.alignChildren = ["fill", "fill"];
            mainGroup.spacing = 10;
            
            // Left: Script list
            var listGroup = mainGroup.add("group");
            listGroup.orientation = "column";
            listGroup.alignment = ["left", "fill"];      // Lock to left, fill vertically
            listGroup.alignChildren = ["fill", "top"];   // Children packed at top
            listGroup.minimumSize = [220, 200];
            listGroup.preferredSize = [260, 300];
            listGroup.maximumSize = [360, 10000];        // Max width 360

            // Single label
            listGroup.add("statictext", undefined, "Scripts:");

            // Single listbox
            var scriptList = listGroup.add("listbox", undefined, [], {multiselect: false});
            scriptList.alignment = ["fill", "fill"];
            scriptList.minimumSize.height = 200;
            
            // Right: Preview and actions
            var previewGroup = mainGroup.add("group");
            previewGroup.orientation = "column";
            previewGroup.alignment = ["fill", "fill"];
            previewGroup.alignChildren = ["fill", "top"];
            previewGroup.minimumSize = [350, 300];   // Min width for preview area
            
            previewGroup.add("statictext", undefined, "Script Preview:");
            
            var infoPanel = previewGroup.add("panel", undefined, "");
            infoPanel.alignment = ["fill", "top"];
            infoPanel.minimumSize.height = 80;
            
            var infoText = infoPanel.add("statictext", undefined, "Select a script to view details", {multiline: true});
            infoText.alignment = ["fill", "fill"];
            infoText.preferredSize.height = 60;
            
            var codePreview = previewGroup.add("edittext", undefined, "", {multiline: true, readonly: true, scrolling: true});
            codePreview.alignment = ["fill", "fill"];
            codePreview.minimumSize.height = 220;
            
            // Action buttons
            var actionGroup = previewGroup.add("group");
            actionGroup.orientation = "row";
            actionGroup.alignment = ["fill", "bottom"];
            actionGroup.alignChildren = ["left", "center"];
            
            var runButton = actionGroup.add("button", undefined, "\u25B6 Run Script");
            runButton.preferredSize.width = 100;
            runButton.enabled = false;
			
			var editScriptButton = actionGroup.add("button", undefined, "\u270F Edit Script");
            editScriptButton.preferredSize.width = 100;
            editScriptButton.enabled = false;
            
            var editButton = actionGroup.add("button", undefined, "\u270E Edit Info");
            editButton.preferredSize.width = 100;
            editButton.enabled = false;
            
            var toggleFavButton = actionGroup.add("button", undefined, "\u2606 Favorite");
            toggleFavButton.preferredSize.width = 100;
            toggleFavButton.enabled = false;
            
            // Bottom toolbar
            var bottomGroup = panel.add("group");
            bottomGroup.orientation = "row";
            bottomGroup.alignment = ["fill", "bottom"];
            bottomGroup.alignChildren = ["left", "center"];
            
            var newScriptButton = bottomGroup.add("button", undefined, "+ New Script");
            var openFolderButton = bottomGroup.add("button", undefined, "\uD83D\uDCC1 Open Folder");
            bottomGroup.add("statictext", undefined, " "); // spacer
            
            // Store references
            panel.searchInput = searchInput;
            panel.categoryDropdown = categoryDropdown;
            panel.favButton = favButton;
            panel.refreshButton = refreshButton;
            panel.scriptList = scriptList;
            panel.infoText = infoText;
            panel.codePreview = codePreview;
            panel.runButton = runButton;
			panel.editScriptButton = editScriptButton;
            panel.editButton = editButton;
            panel.toggleFavButton = toggleFavButton;
            panel.newScriptButton = newScriptButton;
            panel.openFolderButton = openFolderButton;
            
            // Event handlers (unchanged)
            var self = this;
            searchInput.onChanging = function() { self.filterScripts(panel); };
            categoryDropdown.onChange = function() { self.filterScripts(panel); };
            favButton.onClick = function() {
                this.value = !this.value;
                this.text = this.value ? "\u2605 Favorites (On)" : "\u2605 Favorites";
                self.filterScripts(panel);
            };
            favButton.value = false;
            refreshButton.onClick = function() { self.refreshScripts(panel); };
            scriptList.onChange = function() {
                if (this.selection) self.selectScript(panel, this.selection.scriptId);
            };
            scriptList.onDoubleClick = function() {
                if (this.selection) self.executeCurrentScript(panel);
            };
            runButton.onClick = function() { self.executeCurrentScript(panel); };
			editScriptButton.onClick = function() { self.editScriptInQtae(panel); };
            editButton.onClick = function() { self.editMetadata(panel); };
            toggleFavButton.onClick = function() { self.toggleFavorite(panel); };
            newScriptButton.onClick = function() { self.createNewScript(panel); };
            openFolderButton.onClick = function() {
                var folder = new Folder(CONFIG.SCRIPTS_ROOT);
                if (folder.exists) folder.execute();
            };
            
            // Initial load
            this.refreshScripts(panel);
            
            if (panel instanceof Window) {
                panel.center();
                panel.show();
            }
            
            return panel;
        },
        editScriptInQtae: function(panel) {
            if (!this.currentScriptId) return;
            
            var meta = MetadataManager.get(this.currentScriptId);
            var content = readTextFile(meta.file_path);
            
            if (!content) {
                alert("Could not read script file");
                return;
            }
            
            try {
                // ✅ Open qtae window + new tab (same as Python version)
                Python.exec([
                    'from qtae import PythonWindowInstance, ShowPythonWindow',
                    'ShowPythonWindow()',
                    'PythonWindowInstance._add_new_tab(r"' + meta.file_path.replace(/\\/g, '/') + '", """' + content.replace(/"/g, '\\"') + '""")'
                ].join('\n'));
            } catch(e) {
                alert("Failed to open in qtae:\n" + e.toString());
            }
        },
        refreshScripts: function(panel) {
            // **SAVE CURRENT SELECTION**
            var previousScriptId = this.currentScriptId;
            
            MetadataManager.load();
            this.allScripts = ScriptScanner.scan();
            
            // Update category dropdown
            var categories = MetadataManager.getCategories();
            var currentCat = panel.categoryDropdown.selection ? panel.categoryDropdown.selection.text : "All Categories";
            
            panel.categoryDropdown.removeAll();
            panel.categoryDropdown.add("item", "All Categories");
            for (var i = 0; i < categories.length; i++) {
                panel.categoryDropdown.add("item", categories[i]);
            }
            
            // Restore category selection
            for (var i = 0; i < panel.categoryDropdown.items.length; i++) {
                if (panel.categoryDropdown.items[i].text === currentCat) {
                    panel.categoryDropdown.selection = i;
                    break;
                }
            }
            if (!panel.categoryDropdown.selection) {
                panel.categoryDropdown.selection = 0;
            }
            
            this.filterScripts(panel);
            
            // **RESELECT PREVIOUS SCRIPT & REFRESH PREVIEW**
            if (previousScriptId && panel.scriptList.items.length > 0) {
                for (var j = 0; j < panel.scriptList.items.length; j++) {
                    if (panel.scriptList.items[j].scriptId === previousScriptId) {
                        panel.scriptList.selection = j;
                        this.selectScript(panel, previousScriptId);
                        break;
                    }
                }
            }
            
            // **SAFE LAYOUT REFRESH**
            if (panel.layout) {
                panel.layout.layout(true);
            }
        },
        
        filterScripts: function(panel) {
            var searchText = panel.searchInput.text.toLowerCase();
            // SAFE: Handle null selection
            var category = panel.categoryDropdown.selection ? 
                   panel.categoryDropdown.selection.text : 
                   "All Categories";
            var favOnly = panel.favButton.value;
            
            this.filteredScripts = [];
            
            for (var i = 0; i < this.allScripts.length; i++) {
                var script = this.allScripts[i];
                var meta = MetadataManager.get(script.id);
                
                // Search filter
                var matchesSearch = !searchText || 
                    meta.name.toLowerCase().indexOf(searchText) >= 0 ||
                    meta.description.toLowerCase().indexOf(searchText) >= 0 ||
                    this.arrayContains(meta.tags, searchText);
                
                // Category filter
                var matchesCategory = category === "All Categories" || meta.category === category;
                
                // Favorite filter
                var matchesFavorite = !favOnly || meta.favorite;
                
                if (matchesSearch && matchesCategory && matchesFavorite) {
                    this.filteredScripts.push(script);
                }
            }
            
            // Sort: favorites first, then by category, then by name
            this.filteredScripts.sort(function(a, b) {
                var metaA = MetadataManager.get(a.id);
                var metaB = MetadataManager.get(b.id);
                
                if (metaA.favorite !== metaB.favorite) {
                    return metaB.favorite ? 1 : -1;
                }
                
                if (metaA.category !== metaB.category) {
                    return metaA.category < metaB.category ? -1 : 1;
                }
                
                return metaA.name < metaB.name ? -1 : 1;
            });
            
            this.updateScriptList(panel);
        },
        
        updateScriptList: function(panel) {
            panel.scriptList.removeAll();
            this.scriptListItems = [];
            
            for (var i = 0; i < this.filteredScripts.length; i++) {
                var script = this.filteredScripts[i];
                var meta = MetadataManager.get(script.id);
                
                var displayText = (meta.favorite ? "\u2605 " : "\u2606 ") + 
                                meta.name + 
                                " [" + meta.category + "]";
                
                if (meta.tags && meta.tags.length > 0) {
                    displayText += " #" + meta.tags.join(" #");
                }
                
                var item = panel.scriptList.add("item", displayText);
                item.scriptId = script.id;
                this.scriptListItems.push(item);
            }
        },
        
        selectScript: function(panel, scriptId) {
            this.currentScriptId = scriptId;
            var meta = MetadataManager.get(scriptId);
            
            // Update info text
            var infoLines = [];
            infoLines.push(meta.name);
            if (meta.description) infoLines.push(meta.description);
            infoLines.push("Category: " + meta.category);
            if (meta.tags && meta.tags.length > 0) {
                infoLines.push("Tags: " + meta.tags.join(", "));
            }
            if (meta.author) infoLines.push("Author: " + meta.author);
            
            panel.infoText.text = infoLines.join("\n");
            
            // Load code preview
            var code = readTextFile(meta.file_path);
            panel.codePreview.text = code || "# Could not load script";
            
            // Enable buttons
            panel.runButton.enabled = true;
			panel.editScriptButton.enabled = true;
            panel.editButton.enabled = true;
            panel.toggleFavButton.enabled = true;
            panel.toggleFavButton.text = meta.favorite ? "\u2605 Unfavorite" : "\u2606 Favorite";
        },
        
        executeCurrentScript: function(panel) {
            if (!this.currentScriptId) return;
            
            ScriptExecutor.execute(this.currentScriptId);
        },
        
        toggleFavorite: function(panel) {
            if (!this.currentScriptId) return;
            
            var meta = MetadataManager.get(this.currentScriptId);
            meta.favorite = !meta.favorite;
            
            MetadataManager.update(this.currentScriptId, {favorite: meta.favorite});
            
            this.refreshScripts(panel);
        },
        
        editMetadata: function(panel) {
            if (!this.currentScriptId) return;
            
            var meta = MetadataManager.get(this.currentScriptId);
            var allTags = MetadataManager.getAllTags();
            
            var dialog = new Window("dialog", "Edit Script: " + meta.name);
            dialog.spacing = 10;
            dialog.margins = 15;
            
            // Name
            var nameGroup = dialog.add("group");
            nameGroup.add("statictext", undefined, "Name:");
            var nameInput = nameGroup.add("edittext", undefined, meta.name);
            nameInput.characters = 30;
            
            // Description
            dialog.add("statictext", undefined, "Description:");
            var descInput = dialog.add("edittext", undefined, meta.description, {multiline: true});
            descInput.preferredSize = [400, 60];
            
            // Author
            var authorGroup = dialog.add("group");
            authorGroup.add("statictext", undefined, "Author:");
            var authorInput = authorGroup.add("edittext", undefined, meta.author);
            authorInput.characters = 30;
            
            // Tags
            dialog.add("statictext", undefined, "Tags (comma-separated):");
            var tagsInput = dialog.add("edittext", undefined, meta.tags ? meta.tags.join(", ") : "");
            tagsInput.preferredSize.width = 400;
            
            if (allTags.length > 0) {
                var availText = dialog.add("statictext", undefined, "Available: " + allTags.join(", "), {multiline: true});
                availText.preferredSize.width = 400;
                availText.graphics.foregroundColor = availText.graphics.newPen(
                    availText.graphics.PenType.SOLID_COLOR,
                    [0.6, 0.6, 0.6],
                    1
                );
            }
            
            // Favorite
            var favCheck = dialog.add("checkbox", undefined, "Favorite");
            favCheck.value = meta.favorite;
            
            // Buttons
            var buttonGroup = dialog.add("group");
            buttonGroup.alignment = "right";
            var okBtn = buttonGroup.add("button", undefined, "Save", {name: "ok"});
            var cancelBtn = buttonGroup.add("button", undefined, "Cancel", {name: "cancel"});
            
            if (dialog.show() === 1) {
                var tagsStr = tagsInput.text;
                var tagsArray = [];
                if (tagsStr) {
                    var parts = tagsStr.split(",");
                    for (var i = 0; i < parts.length; i++) {
                        var tag = parts[i].replace(/^\s+|\s+$/g, ""); // trim
                        if (tag) tagsArray.push(tag);
                    }
                }
                
                MetadataManager.update(this.currentScriptId, {
                    name: nameInput.text,
                    description: descInput.text,
                    author: authorInput.text,
                    tags: tagsArray,
                    favorite: favCheck.value
                });
                
                this.refreshScripts(panel);
                
                // Reselect
                for (var i = 0; i < panel.scriptList.items.length; i++) {
                    if (panel.scriptList.items[i].scriptId === this.currentScriptId) {
                        panel.scriptList.selection = i;
                        break;
                    }
                }
                
                this.selectScript(panel, this.currentScriptId);
            }
        },
        
        createNewScript: function(panel) {
            var categories = MetadataManager.getCategories();
            
            var dialog = new Window("dialog", "New Script");
            dialog.spacing = 10;
            dialog.margins = 15;
            
            // Name
            var nameGroup = dialog.add("group");
            nameGroup.add("statictext", undefined, "Script Name:");
            var nameInput = nameGroup.add("edittext", undefined, "");
            nameInput.characters = 30;
            
            // Category
            var catGroup = dialog.add("group");
            catGroup.add("statictext", undefined, "Category:");
            var catInput = catGroup.add("edittext", undefined, "Uncategorized");
            catInput.characters = 30;
            
            if (categories.length > 0) {
                var catText = dialog.add("statictext", undefined, "Existing: " + categories.join(", "), {multiline: true});
                catText.preferredSize.width = 400;
            }
            
            // Template
            dialog.add("statictext", undefined, "Template:");
            var templateInput = dialog.add("edittext", undefined, 
                '"""\nScript description here\n"""\n\nimport AEPython as ae\n\n# Your code here\napp = ae.app\n',
                {multiline: true}
            );
            templateInput.preferredSize = [400, 150];
            
            // Buttons
            var buttonGroup = dialog.add("group");
            buttonGroup.alignment = "right";
            var okBtn = buttonGroup.add("button", undefined, "Create", {name: "ok"});
            var cancelBtn = buttonGroup.add("button", undefined, "Cancel", {name: "cancel"});
            
            if (dialog.show() === 1) {
                var name = nameInput.text.replace(/^\s+|\s+$/g, "");
                var category = catInput.text.replace(/^\s+|\s+$/g, "");
                
                if (!name) {
                    alert("Script name is required");
                    return;
                }
                
                if (!category) category = "Uncategorized";
                
                // Create folder
                var categoryFolder = ensureFolder(CONFIG.SCRIPTS_ROOT + "/" + category);
                
                // Create file
                var scriptFile = new File(categoryFolder.fsName + "/" + name + ".py");
                
                if (scriptFile.exists) {
                    alert("Script already exists!");
                    return;
                }
                
                if (!writeTextFile(scriptFile.fsName, templateInput.text)) {
                    alert("Failed to create script file");
                    return;
                }
                
                // Add metadata
                var scriptId = category + "/" + name + ".py";
                MetadataManager.update(scriptId, {
                    name: name,
                    category: category,
                    file_path: scriptFile.fsName,
                    created: MetadataManager.formatDate(new Date())
                });
                
                this.refreshScripts(panel);
                
                // Select new script
                for (var i = 0; i < panel.scriptList.items.length; i++) {
                    if (panel.scriptList.items[i].scriptId === scriptId) {
                        panel.scriptList.selection = i;
                        this.selectScript(panel, scriptId);
                        break;
                    }
                }
                
                alert("Script '" + name + "' created successfully!");
            }
        },
        
        arrayContains: function(arr, searchStr) {
            if (!arr) return false;
            searchStr = searchStr.toLowerCase();
            for (var i = 0; i < arr.length; i++) {
                if (arr[i].toLowerCase().indexOf(searchStr) >= 0) {
                    return true;
                }
            }
            return false;
        }
    };
    
    // =========================================================================
    // PUBLIC API
    // =========================================================================
    
    // FIXED PUBLIC API + PANEL INITIALIZATION
    AEPythonScriptLibrary.showPanel = function() {
        return UIBuilder.buildPanel(null);  // null forces Window
    };
    
    AEPythonScriptLibrary.buildUI = function(thisObj) {
        return UIBuilder.buildPanel(thisObj);
    };
    
    // **CRITICAL: Create dockable panel**
    var panel = (thisObj instanceof Panel) ? thisObj : new Window("palette", CONFIG.WINDOW_TITLE, undefined, {
        resizeable: true
    });
    
    // **BUILD UI ON THE PANEL**
    UIBuilder.buildPanel(panel);
    
    // **CRITICAL: Panel resize handlers**
    panel.layout.layout(true);
    panel.layout.resizeBorder = 5;
    panel.onResizing = panel.onResize = function() { 
        this.layout.resize(); 
        this.layout(true); 
    };
    
    // **ONLY show Window (NOT Panel)**
    if (panel instanceof Window) {
        panel.center();
        panel.show();
    }
    
    // **EXPOSE PANEL GLOBALLY**
    $.global.AEPythonScriptLibrary.panel = panel;
    AEPythonScriptLibrary.panel = panel;
    
    return panel;
    
})(this);