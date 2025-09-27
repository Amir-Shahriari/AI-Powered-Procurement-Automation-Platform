# AI TENDER GENERATOR TESTING GUIDE
## Fleet Vehicle Specifications for Testing

### 🎯 **Testing Purpose**
This guide provides detailed fleet vehicle specifications to test the AI Tender Generator system. The specifications are designed to test both API and local AI functionality.

### 📋 **Available Test Specifications**

#### 1. **Sweeper Truck Specification** (`sweeper_truck_specification_example.md`)
- **Vehicle Type**: Heavy Duty Sweeper Trucks
- **Quantity**: 3 vehicles
- **Contract Value**: $850,000
- **Complexity**: Medium
- **Key Features**: Mechanical broom, vacuum system, dust suppression

#### 2. **Garbage Truck Specification** (`garbage_truck_specification_example.md`)
- **Vehicle Type**: Side Loading Garbage Trucks
- **Quantity**: 5 vehicles
- **Contract Value**: $1,200,000
- **Complexity**: High
- **Key Features**: Automated collection, RFID, compaction system

#### 3. **Fire Truck Specification** (`fire_truck_specification_example.md`)
- **Vehicle Type**: Heavy Duty Fire Trucks
- **Quantity**: 2 vehicles
- **Contract Value**: $2,500,000
- **Complexity**: Very High
- **Key Features**: Fire suppression, rescue equipment, emergency response

### 🚀 **How to Test the AI Tender Generator**

#### **Step 1: Access the Tender Creation Interface**
1. Navigate to the NSW Procurement Platform
2. Sign in to your account
3. Click on **"📋 AI Tender Creation"** in the sidebar
4. Select **"🤖 AI Tender Generator"** tab

#### **Step 2: Input the Specification**
1. **Copy the specification text** from one of the test files
2. **Paste it into the "Project Specifications" text area**
3. **Fill in the basic project details**:
   - Project Title: (e.g., "Sweeper Truck Fleet Replacement")
   - Contract Value: (e.g., "$850,000")
   - Project Type: "Fleet"
   - Council: "Blacktown City Council"

#### **Step 3: Configure AI Settings**
1. **Select AI Model**: Choose between:
   - **Gemini 1.5 Flash** (API - Google)
   - **Local AI Model** (if available)
2. **Enable AI Enhancement**: Check "Use AI for content generation"
3. **Set Generation Parameters**:
   - Creativity Level: Medium
   - Detail Level: High
   - Compliance Focus: High

#### **Step 4: Generate the Tender**
1. Click **"🤖 Generate AI Tender"** button
2. **Monitor the progress** as the AI processes the specification
3. **Review the generated content** in real-time
4. **Wait for completion** (typically 2-5 minutes)

#### **Step 5: Review and Edit**
1. **Examine the generated TEPP document**
2. **Check for accuracy** against the original specification
3. **Verify compliance** with NSW Local Government requirements
4. **Edit any sections** that need adjustment
5. **Save the document** for future reference

### 🔍 **What to Test**

#### **API Testing (Gemini 1.5 Flash)**
- **Response Time**: How quickly does the AI respond?
- **Content Quality**: Is the generated content accurate and relevant?
- **Format Compliance**: Does it follow the TEPP format correctly?
- **Technical Accuracy**: Are technical specifications properly interpreted?
- **Compliance**: Does it meet NSW Local Government standards?

#### **Local AI Testing (if available)**
- **Performance**: How does local AI compare to API?
- **Offline Capability**: Does it work without internet?
- **Privacy**: Is data kept local?
- **Cost**: No API costs for local processing

#### **Specific Test Scenarios**

##### **Test 1: Basic Functionality**
- Use the **Sweeper Truck** specification
- Test with **Gemini 1.5 Flash**
- Verify all sections are generated
- Check for proper formatting

##### **Test 2: Complex Specifications**
- Use the **Fire Truck** specification
- Test with **Local AI** (if available)
- Verify complex technical requirements are handled
- Check for proper evaluation criteria

##### **Test 3: Large Documents**
- Use the **Garbage Truck** specification
- Test with both **API and Local AI**
- Compare response times and quality
- Verify all sections are complete

##### **Test 4: Error Handling**
- Test with **incomplete specifications**
- Test with **malformed text**
- Test with **very long specifications**
- Verify error messages are helpful

### 📊 **Expected Results**

#### **Successful Generation Should Include:**
- ✅ **Complete TEPP Document** with all required sections
- ✅ **Proper Formatting** following NSW Local Government standards
- ✅ **Accurate Technical Specifications** extracted from input
- ✅ **Appropriate Evaluation Criteria** based on project type
- ✅ **Compliance Requirements** for NSW Local Government
- ✅ **Local Preference Policies** for Blacktown City Council
- ✅ **Proper Weightings** for evaluation criteria
- ✅ **Scoring Scales** for each criterion

#### **Quality Indicators:**
- **Accuracy**: Technical specs match input specification
- **Completeness**: All required sections present
- **Compliance**: Meets NSW Local Government requirements
- **Clarity**: Clear and professional language
- **Consistency**: Consistent formatting and structure

### 🐛 **Troubleshooting**

#### **Common Issues and Solutions:**

##### **Issue: AI Generation Fails**
- **Solution**: Check internet connection for API
- **Solution**: Verify API key is valid
- **Solution**: Try with shorter specification text

##### **Issue: Incomplete Content**
- **Solution**: Increase detail level in settings
- **Solution**: Provide more specific project details
- **Solution**: Try with different AI model

##### **Issue: Formatting Problems**
- **Solution**: Check if specification text is well-formatted
- **Solution**: Use the editing interface to fix formatting
- **Solution**: Regenerate with different parameters

##### **Issue: Slow Response**
- **Solution**: Use shorter specification text
- **Solution**: Try local AI if available
- **Solution**: Check system performance

### 📈 **Performance Metrics**

#### **Response Time Targets:**
- **API (Gemini 1.5 Flash)**: 30-120 seconds
- **Local AI**: 60-300 seconds
- **Large Documents**: Up to 5 minutes

#### **Quality Metrics:**
- **Accuracy**: >90% of technical specs correctly interpreted
- **Completeness**: 100% of required sections generated
- **Compliance**: 100% compliance with NSW standards
- **Formatting**: Professional appearance and structure

### 🎯 **Testing Checklist**

#### **Before Testing:**
- [ ] System is running and accessible
- [ ] User account is logged in
- [ ] Test specifications are available
- [ ] AI models are configured
- [ ] Internet connection is stable

#### **During Testing:**
- [ ] Specification is pasted correctly
- [ ] Project details are filled in
- [ ] AI model is selected
- [ ] Generation process is monitored
- [ ] Results are reviewed

#### **After Testing:**
- [ ] Generated content is saved
- [ ] Quality is assessed
- [ ] Issues are documented
- [ ] Performance is measured
- [ ] Feedback is provided

### 📝 **Test Results Template**

```
Test Date: ___________
Tester: ___________
Specification Used: ___________
AI Model: ___________

Response Time: ___________
Content Quality: ___________
Format Compliance: ___________
Technical Accuracy: ___________
Compliance: ___________

Issues Found: ___________
Recommendations: ___________
Overall Rating: ___________
```

### 🔄 **Iterative Testing**

#### **Round 1: Basic Functionality**
- Test with simple specifications
- Verify core features work
- Document any issues

#### **Round 2: Advanced Features**
- Test with complex specifications
- Verify advanced features work
- Compare API vs Local AI

#### **Round 3: Edge Cases**
- Test with edge cases
- Verify error handling
- Test performance limits

#### **Round 4: User Experience**
- Test from user perspective
- Verify ease of use
- Test complete workflow

### 📚 **Additional Resources**

#### **Documentation:**
- AI Tender Generator User Guide
- TEPP Format Specifications
- NSW Local Government Requirements
- Blacktown City Council Standards

#### **Support:**
- Technical Support: support@nswprocurement.gov.au
- User Training: training@nswprocurement.gov.au
- System Issues: issues@nswprocurement.gov.au

---

**Happy Testing! 🚀**

**Remember**: These specifications are for testing purposes only. All details are fictional and for demonstration of the AI Tender Generator system.
