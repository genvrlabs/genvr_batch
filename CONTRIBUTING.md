# Contributing to GenVR Batch Processor

Thank you for your interest in contributing! 🎉

## 🤝 How to Contribute

### Reporting Bugs 🐛

1. **Check existing issues** - Make sure it hasn't been reported
2. **Create a new issue** with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)
   - Screenshots if applicable

### Suggesting Features 💡

1. **Open an issue** with the "enhancement" label
2. Describe:
   - The feature you want
   - Why it would be useful
   - How it should work
   - Mock-ups if you have them

### Submitting Code 🔧

1. **Fork the repository**
2. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly:**
   - Qt version: `python main_qt.py`
   - Tkinter version: `python main.py`
5. **Commit with clear messages:**
   ```bash
   git commit -m "Add: Feature description"
   ```
6. **Push and create Pull Request**

## 📝 Code Style

### Python
- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic

### Example:
```python
def process_batch(self, batch_items):
    """Process batch items with concurrent execution
    
    Args:
        batch_items: List of parameter dicts to process
        
    Returns:
        None (results handled via callbacks)
    """
    # Implementation...
```

## 🧪 Testing

Before submitting:
- ✅ Test on your platform
- ✅ Test with different models
- ✅ Test batch processing
- ✅ Test file uploads (if applicable)
- ✅ Check for errors in console

## 📋 Pull Request Checklist

- [ ] Code follows project style
- [ ] Tested on your platform
- [ ] No console errors
- [ ] Updated README if needed
- [ ] Clear commit messages
- [ ] PR description explains changes

## 🎯 Areas We Need Help

- **Testing on Mac/Linux** - Most development on Windows
- **UI improvements** - Better layouts, icons, themes
- **Performance optimization** - Faster base64 conversion
- **Error handling** - Better error messages
- **Documentation** - Tutorials, videos, guides
- **Translations** - Multi-language support

## 💬 Questions?

- **GitHub Issues** - For bugs and features
- **Discussions** - For questions and ideas

## 🙏 Thank You!

Every contribution helps make this tool better for everyone!

