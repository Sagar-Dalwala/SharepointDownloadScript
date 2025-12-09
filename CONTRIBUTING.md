# 🤝 Contributing Guide

Thank you for considering contributing to the SharePoint/Teams Lecture Video Downloader!

---

## 🎯 Ways to Contribute

### 1. Bug Reports
Found a bug? Help us fix it:
- Search existing issues first
- Provide detailed description
- Include error messages
- Share your configuration (remove sensitive URLs)
- Mention Python & FFmpeg versions

### 2. Feature Requests
Have an idea? We'd love to hear it:
- Check planned features in CHANGELOG.md
- Describe the use case
- Explain the benefit
- Suggest implementation if possible

### 3. Documentation
Help improve docs:
- Fix typos or errors
- Add examples
- Improve clarity
- Translate to other languages
- Add troubleshooting tips

### 4. Code Contributions
Enhance the code:
- Fix bugs
- Add features
- Improve performance
- Add tests
- Refactor code

---

## 🔧 Development Setup

### Prerequisites
```bash
# Clone the repository
git clone <repository-url>
cd SharepointDownloadScript

# Install dependencies
pip install -r scripts/requirements.txt

# Verify setup
python scripts/verify_setup.py
```

### Project Structure
```
IITP/
├── README.md                      # Main documentation
├── QUICKSTART.md                  # Quick setup
├── TROUBLESHOOTING.md             # Issue solutions
├── DOCUMENTATION_INDEX.md         # Navigation
├── CHANGELOG.md                   # Version history
├── IMPLEMENTATION_SUMMARY.md      # Implementation details
├── CONTRIBUTING.md                # This file
└── scripts/
    ├── download_lectures.py       # Main script
    ├── verify_setup.py            # Setup verification
    ├── test_download.py           # Testing utility
    ├── manifest_urls.json         # User config
    ├── manifest_urls.example.json # Template
    └── requirements.txt           # Dependencies
```

---

## 📝 Code Standards

### Python Style
- Follow PEP 8
- Use type hints where possible
- Write descriptive docstrings
- Keep functions focused and small
- Use meaningful variable names

### Example:
```python
def download_video(url: str, output_path: Path, subject: str = "") -> bool:
    """
    Download video using ffmpeg with validation.
    
    Args:
        url: The trimmed videomanifest URL
        output_path: Full path for the output MP4 file
        subject: Subject name (for logging)
    
    Returns:
        True if successful, False otherwise
    """
    # Implementation
```

### Documentation
- Update README.md for new features
- Add examples for new functionality
- Update TROUBLESHOOTING.md for new issues
- Update CHANGELOG.md

---

## 🧪 Testing

### Manual Testing
Before submitting:
1. Run `python scripts/verify_setup.py`
2. Test with real video URLs
3. Test error scenarios
4. Verify notifications work
5. Check documentation updates

### Test Scenarios
- Single video download
- Parallel downloads
- Failed download retry
- URL expiry handling
- Duration validation
- Folder creation

---

## 📤 Submission Process

### 1. Fork & Branch
```bash
# Fork the repository on GitHub
# Clone your fork
git clone <your-fork-url>
cd SharepointDownloadScript

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code
- Add documentation
- Test thoroughly
- Follow code standards

### 3. Commit
```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "Add: Brief description of changes

Detailed explanation of what changed and why.
Fixes #issue-number (if applicable)"
```

### 4. Push & PR
```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Fill in the PR template
# Link related issues
```

---

## 🔍 Pull Request Guidelines

### PR Title
Format: `Type: Brief description`

Types:
- `Add:` New feature
- `Fix:` Bug fix
- `Docs:` Documentation only
- `Refactor:` Code restructuring
- `Test:` Adding tests
- `Perf:` Performance improvement

Examples:
- `Add: Resume download feature`
- `Fix: Duration validation for long videos`
- `Docs: Improve FFmpeg installation guide`

### PR Description
Include:
- What changed
- Why it changed
- How to test
- Related issues
- Screenshots (if UI changes)

### Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Tested locally
- [ ] No errors in console
- [ ] CHANGELOG.md updated

---

## 🐛 Bug Fix Process

### 1. Reproduce
- Understand the issue
- Reproduce locally
- Identify root cause

### 2. Fix
- Write minimal fix
- Add error handling
- Update documentation

### 3. Test
- Verify fix works
- Test edge cases
- Ensure no regression

### 4. Document
- Update TROUBLESHOOTING.md
- Add to CHANGELOG.md
- Comment code if complex

---

## ✨ Feature Development

### Before Starting
1. Check if feature already planned
2. Discuss in issues first
3. Get community feedback
4. Plan implementation

### Implementation
1. Design the feature
2. Update documentation first
3. Write code incrementally
4. Test thoroughly
5. Add examples

### Integration
1. Ensure backward compatibility
2. Update configuration templates
3. Add to QUICKSTART.md if user-facing
4. Update CHANGELOG.md

---

## 📚 Documentation Standards

### Structure
- Clear headings (H1, H2, H3)
- Table of contents for long docs
- Code examples with syntax highlighting
- Screenshots where helpful
- Links to related docs

### Tone
- Friendly and welcoming
- Clear and concise
- Assume user is learning
- Provide examples
- Explain "why" not just "how"

### Code Examples
Always include:
- Setup/prerequisites
- Complete working code
- Expected output
- Explanation

---

## 🎨 UI/UX Guidelines

### Console Output
- Use emojis for visual clarity (✅ ❌ 🎬 📁)
- Color-code status messages
- Show progress indicators
- Clear section separators
- Informative error messages

### User Interaction
- Minimal user input required
- Clear prompts with examples
- Validate user input
- Provide defaults
- Show confirmation messages

---

## 🔐 Security Considerations

### Sensitive Data
- Never commit actual URLs with tokens
- Use placeholders in examples
- Clear instructions for users
- Warn about URL sharing

### Error Messages
- Don't expose full URLs in logs
- Sanitize sensitive information
- Provide helpful but safe errors

---

## 📊 Performance Guidelines

### Optimization
- Use parallel downloads wisely
- Implement timeouts
- Clean up resources
- Handle large files efficiently
- Minimize disk I/O

### Testing
- Test with large files
- Test parallel operations
- Monitor resource usage
- Check memory leaks

---

## 🌟 Recognition

Contributors will be recognized in:
- README.md credits section
- CHANGELOG.md for their contributions
- GitHub contributors page

---

## 📧 Communication

### Questions
- Open an issue for questions
- Use discussions for ideas
- Be respectful and constructive

### Response Time
- We'll respond within 48 hours
- Be patient with reviews
- Provide requested changes promptly

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

## 🙏 Thank You!

Every contribution helps make this tool better for everyone. Whether it's code, documentation, or bug reports - we appreciate your help!

**Happy Contributing! 🚀**
