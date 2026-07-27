from ron_agent.ron_ui import RonApp

if __name__ == "__main__":
    app = RonApp()
    
    # Close PyInstaller splash screen now that UI is loaded
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass
        
    app.mainloop()
