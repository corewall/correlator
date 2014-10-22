//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  DataParser.cpp
// Author   :  Hyejung Hur
// Description: 
//
// Copyright (C) 2007 Hyejung Hur,  
// Electronic Visualization Laboratory, University of Illinois at Chicago
//
// This library is free software; you can redistribute it and/or modify it 
// under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation; either Version 2.1 of the License, or 
// (at your option) any later version.
//
// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
// or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public 
// License for more details.
// 
// You should have received a copy of the GNU Lesser Public License along
// with this library; if not, write to the Free Software Foundation, Inc., 
// 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
//
// Direct questions, comments etc about Correlater Lib to hjhur@evl.uic.edu
//

#include <iostream>
#include <iomanip>
#include <sstream>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

//#include <xercesc/util/PlatformUtils.hpp>
//#include <xercesc/util/TransService.hpp>
//#include <xercesc/parsers/SAXParser.hpp>

#include <DataParser.h>
#include <CoreTypes.h>
#include <Hole.h>
#include <Core.h>
#include <Value.h>
#include <Tie.h>
#include <Section.h>
#include <Strat.h>
#include <GraValue.h>
#include <PwaveValue.h>
#include <NaturalGammaValue.h>
#include <SusceptibilityValue.h>
#include <ReflectanceValue.h>

//#include <XMLLoader.h>

#define NEWOUTPUT 1 // brg 9/8/2014

using namespace std;
static int token_num = 0;

static string DELIMS[] = { " \t", "," };
static string delimiter = DELIMS[SPACETAB];

void SetDelimiter(const int delim)
{
	cout << "SetDelimiter() called with arg " << delim << endl;
	delimiter = DELIMS[delim];
}

static string _coreHeaders[] = { // 13 members
	"Leg", "Site", "Hole", "Core", "CoreType", "Section", "TopOffset",
	"BottomOffset", "Depth", "Data", "RunNo", "RawDepth", "Offset"
};

static string _affineHeaders[] = { // 7 members
	"Leg", "Site", "Hole", "Core No", "Section Type", "Depth Offset", "Y/N"
};

static string _spliceHeaders[] = { // 19 members
	"Site", "Hole", "Core No", "Section Type", "Section No", "Top", "Bottom", "CSF", "CCSF",
	"TIE/APPEND", "Site", "Hole", "Core No", "Section Type", "Section No", "Top", "Bottom", "CSF", "CCSF"
};

static string _ageHeaders[] = { // 13 members
	"Leg", "Site", "Hole", "Core", "CoreType", "Section", "TopOffset",
	"BottomOffset", "Depth", "Data", "SedRate", "Depth(CSF)", "Age(Ma)"
};

static string _stratHeaders[] = { // 22 members
	"No", "Datum Name", "Label", "Type", "Age top", "Age Bottom", "Leg", "Site", "Hole", "Core No",
	"Section Type", "Section No", "Interval", "CSF", "Leg", "Site", "Hole", "Core No", "Section Type",
	"Section No", "Interval", "CSF"
};

static vector<string> ageHeaders(_ageHeaders, _ageHeaders + 13);

static void WriteHeader(const vector<string> headers, int delim)
{}


// Non-POD (Plain Old Data) objects such as std::string cannot be passed in a variable
// argument list! Who knew? Thankfully we can convert std::strings using .c_str().
static void makeDelimString(const string format, string &outStr, ...)
{
	const int argCount = format.length();
	stringstream ss;
	va_list args;
	va_start(args, outStr);
	for (int i = 0; i < argCount; i++) {
		if (format[i] == 'i') {
			int intArg = va_arg(args, int);
			ss << intArg;
		} else if (format[i] == 'f') {
			double floatArg = va_arg(args, double); // float is auto-promoted to double

			// brg 9/9/2014: Match fprintf-style output format - six decimal places
			// filled with zeroes as necessary
			ss << fixed << setprecision(6) << setfill('0') << floatArg;

		} else if (format[i] == 'c') {
			char charArg = va_arg(args, int); // char is auto-promoted to int
			ss << charArg;
		} else if (format[i] == 's') {
			const char *strArg = va_arg(args, const char *);
			ss << strArg;
		}

		if (i + 1 < argCount) // append delimiter for all but last arg
			ss << delimiter;
	}
	outStr = ss.str();
}

Tie* findTie( Data* dataptr, int order );
Strat* findStrat( Data* dataptr, int order );

// separate method for tokenizing internal affine/splice files, which are
// delimited by " \t" for reasons I still don't understand.
int tokenizeLine(char *lineStr, vector<string> &tokens) {
	bool done = false;
	int pos = 0;
	const string line(lineStr);
	while (!done) {
		string token;
		//cout << "search string: " << line.substr(pos) << endl;
		int delimPos = line.find(" \t", pos);
		if (delimPos != string::npos) {
			token = line.substr(pos, delimPos - pos);
			tokens.push_back(token);
			pos = delimPos + 2; // skip past delimiter
		} else { // last token
			delimPos = line.find("\n", pos);
			if (delimPos != string::npos) {
				token = line.substr(pos, delimPos - pos);
				tokens.push_back(token);
			}
			done = true;
		}
		//cout << "#" << token << "#" << endl;
	}
	return 1;
}

int getToken(FILE *fp, char *token)
{
	char seps[] = " ,\t\n{}()";
	int token_idx = 0;

	char curChar;
	bool flag = true;

	while(token_idx == 0 && flag) 
	{
		curChar = fgetc(fp);
		while(curChar != EOF && !strchr(seps, curChar)) 
		{
			token[token_idx] = curChar;
			token_idx++;
			curChar = fgetc(fp);
		}

		if (curChar == EOF)
				flag = false;

		if (strchr("{}()", curChar)) 
		{
			if (token_idx == 0) 
			{
					token[token_idx] = curChar;
					token_idx++;
			} else 
			{
					fseek(fp, -1, SEEK_CUR);
			}
		}
	}

	if (flag == false && token_idx == 0)
			return EOF;

	token[token_idx] = '\0';
	return token_idx;
}

int getToken(char *str, char *token)
{
	char seps[] = " ,\t\n";
    static char token_buf[MAX_TOKENS][TOKEN_LEN];
	//static int token_num = 0;
	static int token_idx = 0;
	char *p_token;

    if (token_num > 0) 
	{
		strcpy(token, token_buf[token_idx]);
		token_num--;
		token_idx++;
	} else 
	{
		if (p_token = strtok(str, seps))
		{
			strcpy(token, p_token);
		} else 
		{
			token[0] = '\0';
			return 0;
		}

		while(p_token = strtok(NULL, seps)) 
		{
			strcpy(token_buf[token_num], p_token);
			token_num++;
			if (token_num > MAX_TOKENS) 
			{
#ifdef DEBUG			
				std::cout << "getToken : token num overflow" << std::endl;
#endif
				_exit(0);
			}
		}
		token_idx = 0;
	}

	return token_num;
}

int getToken(char *str, char *token, char **buf)
{
	char seps[] = " ,\t\n";
	char *p_token;

	//p_token = strtok( str, seps );

#if defined(WIN32) || defined(WIN64)
	if (p_token = strtok_s(str, seps, buf))
	{
		strcpy(token, p_token);
	} else 
	{
		token[0] = '\0';
		return 0;
	}
#else
	if (p_token = strtok_r(str, seps, buf))
	{
		strcpy(token, p_token);
	} else 
	{
		token[0] = '\0';
		return 0;
	}
#endif

	return strlen(token);
}

void toupper(string &str)
{
//	cout << "original string = " << str << endl;
	for (int i = 0; i < str.size(); i++) {
		char c = str[i];
		str[i] = ::toupper(c);
	}
	//cout << "uppercased string = " << str << endl;
	return;
}

void tolower(string &str)
{
//	cout << "original string = " << str << endl;
	for (int i = 0; i < str.size(); i++) {
		char c = str[i];
		str[i] = ::tolower(c);
	}
	//cout << "uppercased string = " << str << endl;
	return;
}

void toupper(char *str)
{
	const int len = strlen(str);
	for (int i=0; i<len; i++) {
		str[i] = ::toupper(str[i]);
	}
	return;
}

void tolower(char *str)
{
	const int len = strlen(str);
	for (int i=0; i<len; i++) {
		str[i] = ::tolower(str[i]);
	}
	return;
}

// convert integer datatype to string
string GetTypeStr(const int datatype, const char *annotation)
{
	string typeStr;
	if (datatype == GRA)
		typeStr = "Bulk Density(GRA)";
	else if (datatype == PWAVE)
		typeStr = "Pwave";
	else if (datatype == SUSCEPTIBILITY)
		typeStr = "Susceptibility";
	else if (datatype == NATURALGAMMA)
		typeStr = "Natural Gamma";
	else if (datatype == REFLECTANCE)
		typeStr = "Reflectance";
	else if (datatype == OTHERTYPE || datatype == USERDEFINEDTYPE) {
		if (annotation != NULL)
			typeStr = string(annotation);
		else
			cout << "annotation is NULL, cannot get user-defined type name" << endl;
	}
	else if (datatype == SPLICE)
		typeStr = "Spliced Records";
	else if (datatype == SPLICED_RECORD)
		typeStr = "Splice Record";
	else if (datatype == ELD_RECORD)
		typeStr = "ELD Record";
	else
		cout << "Unknown data type [" << datatype << "], can't get type string" << endl;
	return typeStr;
}

int FindFormat(const char* filename, FILE *fptr)
{
	string strfile(filename);
	int pos = strfile.find(".xml");
	if(pos != string::npos) 
	{
		return XML_FILE;
	}
	
	pos = strfile.find(".affine.table");
	if(pos != string::npos) 
	{
		return AFFINE_TABLE;
	}
	pos = strfile.find("affine.table");
	if(pos != string::npos) 
	{
		return AFFINE_TABLE;
	}
		
	pos = strfile.find(".affinetable.table");
	if(pos != string::npos) 
	{
		return AFFINE_TABLE1;
	}

	pos = strfile.find(".splice.table");
	if(pos != string::npos) 
	{
		return SPLICE_TABLE;
	}		
	pos = strfile.find("splice.table");
	if(pos != string::npos) 
	{
		return SPLICE_TABLE;
	}
	
	pos = strfile.find(".strat.out");
	if(pos != string::npos) 
	{
		return STRAT_TABLE;
	}	
	
	pos = strfile.find(".strat.table");
	if(pos != string::npos) 
	{
		return STRAT_TABLE;
	}	
		
	pos = strfile.find(".eqlogdepth.table");
	if(pos != string::npos) 
	{
		return EQLOGDEPTH_TABLE;
	}	
	
	pos = strfile.find(".eld");
	if(pos != string::npos) 
	{
		return EQLOGDEPTH_TABLE;
	}	
	
	pos = strfile.find(".eld.table");
	if(pos != string::npos) 
	{
		return EQLOGDEPTH_TABLE;
	}	

	
	pos = strfile.find(".age.out");
	if(pos != string::npos) 
	{
		return AGE;
	}	

	pos = strfile.find(".berger.orb");
	if(pos != string::npos) 
	{
		return BERGER_AGE;
	}	
			
	pos = strfile.find(".splicer.age");
	if(pos != string::npos) 
	{
		return SPLICER_AGE;
	}

	pos = strfile.find(".log.dat");
	if(pos != string::npos) 
	{
		return LOG;
	}

	pos = strfile.find(".ancill.dat");
	if(pos != string::npos) 
	{
		return ANCILL_LOG;
	}

	pos = strfile.find(".spliced.dat");
	if(pos != string::npos) 
	{
		return SPLICE;
	}

	pos = strfile.find(".splicertable.dat");
	if(pos != string::npos) 
	{
		return SPLICER_TABLE;
	}
	
	pos = strfile.find(".logcorepairs.dat");
	if(pos != string::npos) 
	{
		return LOGCORE_PAIRS;
	}
	
	pos = strfile.find(".strat.table");
	if(pos != string::npos) 
	{
		return SPLICER_AGE;
	}
		

	int format = -1;

	//fseek(fptr, 0L, SEEK_SET);

	return format;
}

/*
MST95REPORT
TKREPORT
OSUSCAT
JANUS
JANUSCLEAN
JANUSORIG
ODPOTHER
ODPOTHER1
ODPOTHER2
ODPOTHER3
ODPOTHER4
ODPOTHER5
*/

int FindCoreType(FILE *fptr, int format)
{
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	int type =OTHERTYPE;
	if(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		int count=0;
		while(getToken(line, token) > 0) count++;

		if(format == MST95REPORT)
		{
#ifdef DEBUG
	cout << "[MST95report] Token Count : " << count << endl;
#endif	
			switch(count) 
			{
			case 12  : type = GRA; break; // todo : ??????
			case 13  : type = PWAVE; break;
			case 11  : type = SUSCEPTIBILITY; break;
			case 16  : type = NATURALGAMMA; break;
			case 45  : type = REFLECTANCE; break;
			default : type = OTHERTYPE;
			}
		}	
		else if (format == TKREPORT)
		{
#ifdef DEBUG
	cout << "[TKreport] Token Count : " << count << endl;
#endif	
			switch(count) 
			{
			case 9   : type = SUSCEPTIBILITY; break; // todo : ??????
			case 13  : type = PWAVE; break;
			case 11  : type = SUSCEPTIBILITY; break;
			case 16  : type = NATURALGAMMA; break;
			case 45  : type = REFLECTANCE; break;
			default : type = OTHERTYPE;
			}
		}
	}
	fseek(fptr, 0L, SEEK_SET);

	return type;
}

bool IsAlphabet(char* token)
{
	if (token == NULL) return false;
	
	int length = strlen(token);
	for(int i =0; i < length; i++)
	{
		if (isalpha(token[i]) == 0) 
		{
			return false;
		}
	}
	return true;	
}

int ReadCoreFormat(FILE *fptr, Data* dataptr, int datatype, char* annotation)
{
	if(dataptr == NULL) return 0;

#ifdef DEBUG	
	if(annotation != NULL)
		cout << "annotation =" << annotation << endl;
#endif	
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);

	int type = datatype;

	// check core type :
	// GRA PWAVE SUSCEPTIBILITY NATURALGAMMA REFLECTANCE OTHERTYPE
	//int datatype = FindCoreType(fptr, MST95REPORT); 
	dataptr->setType(datatype);

	type = INTERNAL_TYPE;

	Hole* newHole = NULL;
	char hole_name[16];
	int hole_index = dataptr->getNumOfHoles() -1;
	//cout << "[Internal Format] hole index : " << hole_index << "\n" << endl;

	Core* newCore = NULL;
	int core_index;
	int prev_core_index = -1;
	
	Section* newSection = NULL;
	int section_index;	
	
	Value* newValue = NULL;
	int value_index;
	
	char sec_type;
	char section[2];
	double depth;
	
	bool bCore;
	bool bSection;
	bool bValidate;
	char prev_hole_name[16];
	memset(prev_hole_name, 0, 10);
	char* name_ptr;
	double prev_top = -999.0;
	int process_count = 0;
					
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		bValidate = true;
		// set leg, subleg(?), site
		getToken(line, token);				
		if(token[0] == '#')
		{
			token_num = 0;
			continue;
		}
		dataptr->setLeg(token);
		
		getToken(line, token);					
		dataptr->setSite(token);	
		
		// hole name
		getToken(line, token);				
		toupper(&token[0]);		
		memset(hole_name, 0, 16);
		strcpy(hole_name, token);
		
		if (strcmp(hole_name, prev_hole_name) != 0)
		{
			// check if new hole
			newHole = dataptr->getHole(&hole_name[0], MST95REPORT, datatype, annotation);
			if(newHole == NULL) 
			{
				hole_index++;			
				// create new Hole  
				newHole = dataptr->createHole(hole_index, &hole_name[0], datatype, annotation);
				if(newHole == NULL) return 0;
				newHole->setDataFormat(MST95REPORT);				
				newHole->setType(datatype);

				if (datatype == USERDEFINEDTYPE) 
				{
					newHole->setAnnotation(annotation);
				}
			}	
		}
		//prev_hole_name = hole_name;			
		memset(prev_hole_name, 0, 10);
		strcpy(prev_hole_name, token);
		
		// core index
		getToken(line, token);
		if (IsAlphabet(token) == true) 
		{
#ifdef DEBUG		
			cout << "[ERROR] Core ID : Expect Number is not Alphabet " << endl;
#endif
			token_num = 0;
			continue;
		}
		core_index = atoi(token);
		if(prev_core_index != -1)
		{
			for(int k=prev_core_index+1; k < core_index; k++)
			{
				newCore = newHole->getCoreByNo(k);
				if(newCore == NULL)
				{
					newCore = newHole->createCore(k);
					newCore->setNumber(k);
					newCore->setType(datatype);
#ifdef DEBUG					
					cout << "[DEBUG] Extra Core is created : No. " << k << endl;
#endif
				}
			}
		}
		
		newCore = newHole->getCoreByNo(core_index);
		if(newCore == NULL)
		{
			newCore = newHole->createCore(core_index);
			newCore->setNumber(core_index);	
			newCore->setType(datatype);	
			value_index = 0;
			bCore = true;
		} else 
		{
			value_index = newCore->getNumOfValues();
			bCore = false;
		}
		prev_core_index = core_index;
		
		// value type
		getToken(line, token);		
		toupper(&token[0]);
		sec_type = token[0];
		//newValue->setType(token[0]);

		// section info
		getToken(line, token);
		toupper(&token[0]);	
		strcpy(section, token);
		if ((token[0] >= '0') && (token[0] <= '9'))
		{
			section_index = atoi(token);
		} else 
		{
#ifdef DEBUG		
			cout << "[DataManager] section number is not integer : " << token << endl;
#endif
			token_num = 0;
			continue;		
		}
		//newValue->setSection(token);
		 
		// top, bottom
		data_range range;
		getToken(line, token);	
		if ((token[0] != '-') && (strcmp(token, "null") != 0))
		{	
			range.top = atof(token);	
			
			if((value_index == 0) && (prev_top < range.top))
				process_count++;
			
			prev_top = range.top;
		} 
		getToken(line, token);	
		if ((token[0] != '-') && (strcmp(token, "null") != 0))
		{		
			range.bottom = atof(token);	
		}
		
		// depth
		getToken(line, token);
		if((token[0] != '-') && (strcmp(token, "null") == 0))
		{
#ifdef DEBUG		
			cout << "[ERROR] Depth : " << token << endl;
#endif
			token_num = 0;
			continue;		
		}
		if (IsAlphabet(token) == true) 
		{
#ifdef DEBUG		
			cout << "[ERROR] Depth : Expect Number is not Alphabet " << endl;
#endif
			if(bCore == true)
			{
				newHole->deleteCore(core_index);
			}	
			token_num = 0;
			continue;
		}		
		depth = atof(token);
		if(strcmp(hole_name, "SPLICED_RECORD") == 0)
		{
			newValue = newCore->createValue(value_index);
		} else 
			newValue = newCore->createValue(value_index, depth);
		if(newValue == NULL) continue;
		newValue->setType(sec_type);
		newValue->setSection(section);
		newSection = newCore->getSection(section_index);
		if(newSection == NULL)
		{
			//section_index = atoi(token);
			newSection = newCore->createSection(section_index);		

			if(newSection != NULL)
			{
				newSection->setStartValue(newValue);
			}
			bSection = true;
		} else 
		{
			newSection->setEndValue(newValue);
			bSection = false;
		}
		newValue->setRange(range);
		newValue->setDepth(depth);
		newValue->setMbsf(depth);
		
		if((depth < 0.0) && (core_index > 0))
		{
			bValidate = false;
		}
		
		// get data
		getToken(line, token);				
		if((token[0] != '-') && (strcmp(token, "null") == 0))
		{
			value_index--;
			bValidate = false;
		}
		if (IsAlphabet(token) == true) 
		{
#ifdef DEBUG		
			cout << "[ERROR] Data : Expect Number is not Alphabet " << endl;
#endif
			bValidate = false;
		}		
		
		if(bValidate == false)
		{
			if((bCore == true) && (bSection == true))
			{
				newHole->deleteCore(core_index);
#ifdef DEBUG
				cout << "[DEBUG] CORE " << core_index << " is DELETED " << endl;
#endif
				newCore = NULL;
			} else
			{
				if(bSection == true)
				{
					newCore->deleteSection(section_index);	
#ifdef DEBUG					
					cout << "[DEBUG] SECTION " << section_index << " is DELETED " << endl;
#endif					
					newSection = NULL;
				} 
				if(newValue)
				{
					newCore->deleteValue(newValue->getNumber());
#ifdef DEBUG					
					cout << "[DEBUG] VALUE is DELETED " << endl;
#endif					
					newValue = NULL;
				}			
			}
		} else 
		{
			NaturalGammaValue* pValue = (NaturalGammaValue*) newValue;
			pValue->setTotalCount(atof(token));			

			getToken(line, token);				
			pValue->setRunNo(atoi(token));
		}

		token_num = 0;
	}
	
	if((newHole != NULL) && (process_count > 1))
	{
		newHole->setTopAvailable(false);
#ifdef DEBUG		
		cout << "[DEBUG] TOP/BOTTOM data is missing for " << newHole->getName() << " : " << process_count << endl;
#endif
	}
	
	return 1;
}
   

int ReadIODPAffineTable(FILE *fptr, Data* dataptr)
{
	if(dataptr == NULL) return 0;

	char line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char value_type;
	int nholeA, coreidA, numHoles;
	char* holeA;

	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		vector<string> tokens;
		tokenizeLine(line, tokens);
		int tokenIndex = 0;

		string token = tokens[tokenIndex++];
		if (token[0] == '#') // skip comment line
			continue;

		// ensure file site matches loaded holes' site (IODP format excludes leg)
		if (strcmp(dataptr->getSite(), token.c_str()) != 0)
		{
			cout << "site name [" << token << "] does not match loaded site [" << dataptr->getSite() << "], bailing" << endl;
			continue;
		}

		token = tokens[tokenIndex++];
		toupper(token);
		Hole *newHole = dataptr->getHole((char *)token.c_str()); // finds first hole whose name matches, whatever its data type
		if (newHole == NULL)
		{
			cout << "hole name [" << token << "] does not match loaded any holes in site [" << dataptr->getSite() << "], bailing" << endl;
			token_num = 0;
			continue;
		}
		holeA = (char*) newHole->getName();
		nholeA = dataptr->getNumOfHoles(holeA); // count all holes (any data type) whose name matches holeA

		// core number
		token = tokens[tokenIndex++];
		Core *newCore = newHole->getCoreByNo(atoi(token.c_str()));
		if (newCore == NULL)
		{
			cout << "core number [" << token << "] not found in hole [" << newHole->getName() << "], bailing" << endl;
			continue;
		}
		coreidA = newCore->getNumber();

		token = tokens[tokenIndex++];
		toupper(token);
		value_type = token[0];

		token = tokens[tokenIndex++];
		const double mbsfDepth = atof(token.c_str()); // CSF in IODP terms

		token = tokens[tokenIndex++];
		const double mcdDepth = atof(token.c_str()); // CCSF in IODP terms

		token = tokens[tokenIndex++];
		const double cumOffset = atof(token.c_str()); // cumulative offset

		token = tokens[tokenIndex++];
		const double diffOffset = atof(token.c_str()); // differential offset

		token = tokens[tokenIndex++];
		const double growthRate = atof(token.c_str()); // growth rate

		token = tokens[tokenIndex++];
		int shiftType = -1;
		if (strcmp(token.c_str(), AFFINE_TIE_STR) == 0)
			shiftType = AFFINE_TIE;
		else if (strcmp(token.c_str(), AFFINE_SET_STR) == 0)
			shiftType = AFFINE_SET;
		else if (strcmp(token.c_str(), AFFINE_ANCHOR_STR) == 0)
			shiftType = AFFINE_ANCHOR;
		else {
			cout << "Unknown affine shift type [" << token << "], skipping" << endl;
			continue;
		}

		token = tokens[tokenIndex++];
		const string affineDatatype = token;
		token = tokens[tokenIndex++];
		const string qualityComment = token;

		Value *newValue = newCore->getValue(0);
		if (newValue)
			value_type = newValue->getType();

		const bool fromFile = true;
		const bool applied = (shiftType != AFFINE_ANCHOR);
		newCore->setDepthOffset(diffOffset, value_type, applied, fromFile);
		newCore->setAffineType(shiftType);
		newCore->setAffineDatatype(affineDatatype);
		newCore->setComment(qualityComment);

		numHoles = dataptr->getNumOfHoles();

		// affine values have been applied to the hole we found above, whatever its data type.
		// Now do the same for all *other* holes with that name, but with other data types.
		for (int i=1; i < nholeA; i++)
		{
			int count = 0;
			for (int j=0; j < numHoles; j++)
			{
				newHole = dataptr->getHole(j);
				char *temp_hole_name = (char*) newHole->getName();
				if (strcmp(temp_hole_name,holeA) == 0)
				{
					if (count == i)
					{
						newCore = newHole->getCoreByNo(coreidA);
						if (newCore)
						{
							newCore->setDepthOffset(diffOffset, value_type, applied, fromFile);
							newCore->setAffineType(shiftType);
							newCore->setAffineDatatype(affineDatatype);
							newCore->setComment(qualityComment);
						}
						break;
					}
					count++;
				}
			}
		}
	}

	return 1;
}

int ReadAffineTable(FILE *fptr, Data* dataptr)
{
	if(dataptr == NULL) return 0;

	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	Hole* newHole = NULL;
	Core* newCore = NULL;
	Value* newValue = NULL;
	
	double depth_offset;
	char value_type;
	int nholeA, coreidA, numHoles;
	char* holeA;
	
	bool applied, fromfile;
	int count =0;
	char* temp_hole_name = NULL;
	int affinetype;
	
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		// check leg
		getToken(line, token);	
		if(token[0] == '#')
		{
			token_num = 0;
			continue;
		}		
								
		if(strcmp(dataptr->getLeg(), token) !=0) 
		{
			token_num = 0;
			continue;
		}		

		// check site
		getToken(line, token);				
		if(strcmp(dataptr->getSite(), token) !=0)
		{
			token_num = 0;
			continue;
		}		

		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		temp_hole_name = &token[0];
		newHole = dataptr->getHole(temp_hole_name); // finds first hole whose name matches, whatever its data type
		if(newHole == NULL) 
		{
			token_num = 0;
			continue;
		}
		holeA = (char*) newHole->getName();
		nholeA = dataptr->getNumOfHoles(holeA); // count all holes (any data type) whose name matches holeA
		
		// check core number
		getToken(line, token);	
		newCore = newHole->getCoreByNo(atoi(token));
		if(newCore == NULL) 
		{
			token_num = 0;
			continue;
		}
		coreidA = newCore->getNumber();

		// type
		getToken(line, token);	
		toupper(&token[0]);	
		value_type = token[0];
		
		getToken(line, token);	
		depth_offset = atof(token);
		getToken(line, token);		
		toupper(&token[0]);	
		if(token[0] == 'Y')
		{ 
			applied = true;
			affinetype = 1;
			fromfile = true;
		} else if (token[0] == 'N')
		{
			applied = false;
			if(depth_offset != 0)
			{
				applied = true;
			}
			affinetype = 0;
			fromfile = true;		
		}
		
		newValue = newCore->getValue(0);
		if(newValue)
			value_type = newValue->getType();
		
		newCore->setDepthOffset(depth_offset, value_type, applied, fromfile);
		newCore->setAffineType(affinetype);
		
		numHoles = dataptr->getNumOfHoles();

		// affine values have been applied to the hole we found above, whatever its data type.
		// Now do the same for all *other* holes with that name, but with other data types.
		for(int i=1; i < nholeA; i++)
		{
			count = 0;
			for(int j=0; j < numHoles; j++)
			{
				newHole = dataptr->getHole(j);
				temp_hole_name = (char*) newHole->getName();
				if(strcmp(temp_hole_name,holeA) == 0)
				{	
					if(count == i)
					{
						newCore = newHole->getCoreByNo(coreidA);
						if(newCore)
						{
							newCore->setDepthOffset(depth_offset, value_type, applied, fromfile);
							newCore->setAffineType(affinetype);
						}
						break;
					}
					count++;
				} 
			}
		}			
		
		
		token_num = 0;	
	}
	
	return 1;
}

double getData(Value* prev_valueptr, Value* next_valueptr, double depth)
{
	//double diff_depth = next_valueptr->getELD() - prev_valueptr->getELD();
	double diff_depth = next_valueptr->getMcd() - prev_valueptr->getMcd();

	double diff_data = next_valueptr->getData() - prev_valueptr->getData();
	
	if (diff_data == 0)
		return next_valueptr->getData();
	if (diff_depth == 0)
		return next_valueptr->getData();

		
	double a = diff_depth / diff_data;
	//double b = next_valueptr->getELD() - a * next_valueptr->getData();
	double b = next_valueptr->getMcd() - a * next_valueptr->getData();
	
	double ret = (depth - b) / a;
	return ret;
}

int ReadSpliceTable(FILE *fptr, Data* dataptr, bool alternative, int core_type, char* annotation)
{
	if(dataptr == NULL) return 0;
	
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	Hole* newHole = NULL;
	if(core_type == -1)
	{
		newHole = dataptr->getHole(0);
		core_type = newHole->getType();
		if (core_type == USERDEFINEDTYPE)
			annotation = (char*) newHole->getAnnotation();
			
	}
		
	Core* newCore = NULL;
	Core* coreptr = NULL;
	Tie* tieptr = NULL;
	Tie* temp_tieptr = NULL;
	char type;
	char section[2];
	memset(section, 0, 2);
	data_range range;
	data_range rangeA, rangeB;
	double mbsf, mcd;
	TieInfo* infoTied = NULL;
	int order = 0;
	bool appendflag = false;
	bool allflag = false;
	double prevmcd;
	int tie_type = REAL_TIE;
	if (alternative == true)
	{
		tie_type = ALT_REAL_TIE;
	}
	char* temp_hole_name = NULL;
	std::vector<Tie*>::iterator iter;	
	std::vector<Tie*> temp_list;	
	
	double depth;
	Value* newValue = NULL;
	Value* temp_newValue  = NULL;
	double temp_data;
	double temp_top;
	int idx;
	Value* valueA;
	Value* valueB;
	Tie* tieptr_temp;
		
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		// check site
		getToken(line, token);
		if(token[0] == '#')
		{
			token_num = 0;
			continue;
		}
					
		if(strcmp(dataptr->getSite(), token) !=0) 
		{
			token_num = 0;
			dataptr->init(tie_type);
#ifdef DEBUG			
			cout << "return -------->" << endl;
#endif
			return 0;
		}
			
		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		temp_hole_name = &token[0];
		newHole = dataptr->getHole(temp_hole_name, core_type, annotation);
		if(newHole == NULL)
		{
#ifdef DEBUG		
			cout << "1 could not find hole " << endl;
#endif
			token_num = 0;
			dataptr->init(tie_type);
			return 0;
		}

		// check core number
		getToken(line, token);	
		newCore = newHole->getCoreByNo(atoi(token));
		if(newCore == NULL) 
		{
			token_num = 0;
			continue;
		}
		coreptr = newCore;
		
		// type
		getToken(line, token);	
		toupper(&token[0]);	
		type = token[0];
		
		// section
		getToken(line, token);	
		toupper(&token[0]);
		strcpy(section, token);
		
		// top - bottom
		getToken(line, token);		
		range.top = atof(token);
		getToken(line, token);		
		range.bottom = atof(token);
			
		// mbsf
		getToken(line, token);		
		mbsf = atof(token);
	
		// mcd
		getToken(line, token);		
		mcd = atof(token);
	
		getToken(line, token);		
		toupper(&token[0]);
		if((token_num) == 0 && tieptr)
		{	
			tieptr->setAppend(true, true);	
			//order++;	
			continue;	
		}

		if(strcmp(token, "TIE") != 0 && strcmp(token, "APPEND") != 0)
		{
			token_num = 0;
			continue;
		}	
		appendflag = false;
		allflag = false;	
		if(strcmp(token, "APPEND") == 0)
		{
			appendflag = true;
			/*allflag = false;		
			if((range.top >= 9999.0) && (range.bottom <= -9999.0))
			{
				allflag = false;
			}*/			
		}
		
		// check site
		getToken(line, token);
		if((token_num == 0) && tieptr)
		{
			allflag = true;		
			tieptr->setAppend(appendflag, allflag);		
			//order++;
			token_num = 0;
			continue;	
		}
							
		if(strcmp(dataptr->getSite(),token) !=0) 
		{
			token_num = 0;
			continue;
		}	
			
		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		temp_hole_name = &token[0];
		newHole = dataptr->getHole(temp_hole_name, core_type, annotation);		
		if(newHole == NULL)  
		{
#ifdef DEBUG		
			cout << "2 could not find hole " << endl;
#endif
			token_num = 0;
			continue;
		}

		// check core number
		getToken(line, token);	
		newCore = newHole->getCoreByNo(atoi(token));
		if(newCore == NULL)
		{
			token_num = 0;
			continue;
		}
		
		if((appendflag == true) && (allflag == false))
		{
			//tieptr = new Tie(tie_type);
			tieptr = new Tie(coreptr, type, section, range, mbsf, mcd, tie_type, true);		
			valueA  = tieptr->getTiedValue();
			//std::cout << "P/a) " << valueA->getMbsf() << " " << valueA->getMcd() << std::endl;
			if(valueA && valueA->getMcd() != range.top)
			{
				depth = mbsf;
				//double offset = posB- posA;
				idx = valueA->getNumber();
				temp_data = valueA->getRawData();
				if(depth <  valueA->getMbsf())
				{
					temp_newValue = coreptr->getValue(idx-1);
					if(temp_newValue)
					{
						temp_data= getData(temp_newValue, valueA, mcd); 
					} 
				} else 
				{
					temp_newValue = coreptr->getValue(idx+1);
					if(temp_newValue)
					{
						temp_data = getData(valueA, temp_newValue, mcd); 				
					}						
				}		

				newValue = coreptr->createInterpolatedValue(depth);
				if(newValue && (newValue->getMbsf() != depth))
				{
					newValue->copy(valueA);
					newValue->setValueType(INTERPOLATED_VALUE); // this is assigned in createInterpolatedValue(), but lost when we copy valueA into newValue
					newValue->setDepth(depth);
					newValue->applyAffine(coreptr->getDepthOffset(), newValue->getType());
					//newValue->setB(offset);
					// need to update data and bottom/top value
					newValue->setRawData(temp_data);
					newValue->setTop(range.top);
					valueA = newValue;
					//std::cout << "P/a)--> new value is created.... "  << newValue->getTop() << " " << newValue->getMbsf() << ", " << newValue->getMcd() << std::endl;
				}
			}
			tieptr->setTied(valueA);
						
			prevmcd = mcd;			
			coreptr->addTie(tieptr);
			temp_list.push_back(tieptr);

			//data_range range;
			//tieptr->setTied(newCore, type, section, range);	

			// type
			getToken(line, token);	
			toupper(&token[0]);	
			type = token[0];
			
			// section
			getToken(line, token);	
			toupper(&token[0]);
			strcpy(section, token);
				
			// top - bottom
			getToken(line, token);		
			range.top = atof(token);
			getToken(line, token);		
			range.bottom = atof(token);
			
			// mbsf
			getToken(line, token);		
			mbsf = atof(token);
		
			// mcd
			getToken(line, token);		
			mcd = atof(token);
						
			tieptr->setTieTo(newCore, type, section, range, mbsf, mcd);
			valueB  = tieptr->getTieToValue();
			if(valueB && valueB->getMcd() != range.top)
			{
				//std::cout << "P/b) " << valueB->getMbsf() << " " << valueB->getMcd() << std::endl;			
				depth = mbsf;
				//double offset = posB- posA;
				idx = valueB->getNumber();
				temp_data = valueB->getRawData();
				if(depth <  valueB->getMbsf())
				{
					temp_newValue = newCore->getValue(idx-1);
					if(temp_newValue)
					{
						temp_data= getData(temp_newValue, valueB, mcd); 
					}
				} else 
				{
					temp_newValue = newCore->getValue(idx+1);
					if(temp_newValue)
					{
						temp_data = getData(valueB, temp_newValue, mcd); 			
					}			
				}		
				newValue = newCore->createInterpolatedValue(depth);
				if(newValue && (newValue->getMbsf() != depth))
				{
					newValue->copy(valueB);
					newValue->setValueType(INTERPOLATED_VALUE); // this is assigned in createInterpolatedValue(), but lost when we copy valueB into newValue
					newValue->setDepth(depth);
					newValue->applyAffine(newCore->getDepthOffset(), newValue->getType());
					//newValue->setB(offset);
					// need to update data and bottom/top value
					newValue->setRawData(temp_data);
					newValue->setTop(range.top);
					valueB = newValue;
					//std::cout << "P/b)--> new value is created.... "  << newValue->getTop() << " " << newValue->getMbsf() << ", " << newValue->getMcd() << std::endl;
				}
			}
			tieptr->setTieTo(valueB);		
			//std::cout << "P/a=) " << valueA->getMbsf() << " " << valueA->getMcd() << " " << valueA->getNumber() << std::endl;		
			//std::cout << "P/b=) " << valueB->getMbsf() << " " << valueB->getMcd() << " " << valueB->getNumber() << std::endl;	

			rangeA.top = valueA->getTop();
			rangeA.bottom = range.top;
			rangeB.top = valueB->getTop();
			rangeB.bottom = rangeB.top;		
			tieptr->setTied(coreptr, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), valueA->getMcd());
			tieptr->setTieTo(newCore, valueB->getType(), valueB->getSection(), rangeB, valueB->getMbsf(), valueB->getMcd());
			
			valueA  = tieptr->getTiedValue();
			//std::cout << "P/a) " << valueA->getMbsf() << " " << valueA->getMcd() << " " << valueA->getNumber() << std::endl;		
			valueB  = tieptr->getTieToValue();
			//std::cout << "P/b) " << valueB->getMbsf() << " " << valueB->getMcd() << " " << valueB->getNumber() << std::endl;			
	
			
			
			if(tieptr->getTieToValue() == NULL || tieptr->getTiedValue() == NULL)
			{
				//cout << mcd << " " << tieptr->getTieToValue()->getMcd() <<  " " << tieptr->getTiedValue()->getMcd() << endl;
				
				if(tieptr->getTiedValue() == NULL)
				{
					infoTied = tieptr->getInfoTied();
#ifdef DEBUG					
					cout << "[DEBUG/ERROR:READSPLICETABLE] Could not find value at TIED " << infoTied->m_coreptr->getName() << infoTied->m_coreptr->getNumber() << endl;
#endif
				} else 
				{
					infoTied = tieptr->getInfoTieTo();
#ifdef DEBUG
					cout << "[DEBUG/ERROR:READSPLICETABLE] Could not find value at TIETO " << infoTied->m_coreptr->getName() << infoTied->m_coreptr->getNumber() << endl;
#endif
				}
				for(iter = temp_list.begin(); iter != temp_list.end(); iter++)
				{
					temp_tieptr = (Tie*) *iter;
					if(temp_tieptr == NULL) continue; 
					
					infoTied = temp_tieptr->getInfoTied();
					infoTied->m_coreptr->deleteTie(temp_tieptr->getId());
					delete temp_tieptr;
					temp_tieptr = NULL;
				}
				return -1;
			}

			//tieptr->setTieTo(coreptr,  type, section, range);	
			//newCore->addTie(tieptr);
		} else 
		{

			// create Tie and add
			tieptr = new Tie(coreptr, type, section, range, mbsf, mcd, tie_type, true);		
			valueA  = tieptr->getTiedValue();
			//std::cout << "P/a) " << valueA->getMbsf() << " " << valueA->getMcd() << std::endl;
			if(valueA && valueA->getMcd() != range.top)
			{
				depth = mbsf;
				//double offset = posB- posA;
				idx = valueA->getNumber();
				temp_data = valueA->getRawData();
				if(depth <  valueA->getMbsf())
				{
					temp_newValue = coreptr->getValue(idx-1);
					if(temp_newValue)
					{
						temp_data= getData(temp_newValue, valueA, mcd); 
					} 
				} else 
				{
					temp_newValue = coreptr->getValue(idx+1);
					if(temp_newValue)
					{
						temp_data = getData(valueA, temp_newValue, mcd); 				
					}						
				}		
				newValue = coreptr->createInterpolatedValue(depth);

				if(newValue && (newValue->getMbsf() != depth))
				{
					newValue->copy(valueA);
					newValue->setValueType(INTERPOLATED_VALUE); // this is assigned in createInterpolatedValue(), but lost when we copy valueA into newValue
					newValue->setDepth(depth);
					newValue->applyAffine(coreptr->getDepthOffset(), newValue->getType());
					//newValue->setB(offset);
					// need to update data and bottom/top value
					newValue->setRawData(temp_data);
					newValue->setTop(range.top);
					valueA = newValue;
					//std::cout << "P/a)--> new value is created.... "  << newValue->getTop() << " " << newValue->getMbsf() << ", " << newValue->getMcd() << std::endl;
				}
			}
			if(valueA == NULL) continue;

			tieptr->setTied(valueA);
						
					
			prevmcd = mcd;
			//tieptr->setOrder(order);
			coreptr->addTie(tieptr);
			//tieptr->setAppend(appendflag, allflag);
			temp_list.push_back(tieptr);
							
			// type
			getToken(line, token);	
			toupper(&token[0]);	
			type = token[0];
			
			// section
			getToken(line, token);	
			toupper(&token[0]);
			strcpy(section, token);
				
			// top - bottom
			getToken(line, token);		
			range.top = atof(token);
			getToken(line, token);		
			range.bottom = atof(token);
			
			// mbsf
			getToken(line, token);		
			mbsf = atof(token);
		
			// mcd
			getToken(line, token);		
			mcd = atof(token);

			// create Tie and add
			tieptr->setTieTo(newCore, type, section, range, mbsf, mcd);
			valueB  = tieptr->getTieToValue();
			
			if(valueB && valueB->getMcd() != range.top)
			{
				//std::cout << "P/b) " << valueB->getMbsf() << " " << valueB->getMcd() << std::endl;			
				depth = mbsf;
				//double offset = posB- posA;
				idx = valueB->getNumber();
				temp_data = valueB->getRawData();
				if(depth <  valueB->getMbsf())
				{
					temp_newValue = newCore->getValue(idx-1);
					if(temp_newValue)
					{
						temp_data= getData(temp_newValue, valueB, mcd); 
					}
				} else 
				{
					temp_newValue = newCore->getValue(idx+1);
					if(temp_newValue)
					{
						temp_data = getData(valueB, temp_newValue, mcd); 			
					}			
				}
		
				newValue = newCore->createInterpolatedValue(depth);
				if(newValue && (newValue->getMbsf() != depth))
				{
					newValue->copy(valueB);
					newValue->setValueType(INTERPOLATED_VALUE); // this is assigned in createInterpolatedValue(), but lost when we copy valueA into newValue
					newValue->setDepth(depth);
					newValue->applyAffine(newCore->getDepthOffset(), newValue->getType());
					//newValue->setB(offset);
					// need to update data and bottom/top value
					newValue->setRawData(temp_data);
					newValue->setTop(range.top);
					valueB = newValue;
					//std::cout << "P/b)--> new value is created.... "  << newValue->getTop() << " " << newValue->getMbsf() << ", " << newValue->getMcd() << std::endl;
				}
			}
			if(valueB == NULL) continue;

			tieptr->setTieTo(valueB);		
			//std::cout << "P/a=) " << valueA->getMbsf() << " " << valueA->getMcd() << " " << valueA->getNumber() << std::endl;		
			//std::cout << "P/b=) " << valueB->getMbsf() << " " << valueB->getMcd() << " " << valueB->getNumber() << std::endl;	
							
			rangeA.top = valueA->getTop();
			rangeA.bottom = range.top;
			rangeB.top = valueB->getTop();
			rangeB.bottom = rangeB.top;		
			tieptr->setTied(coreptr, valueA->getType(), valueA->getSection(), rangeA, valueA->getMbsf(), valueA->getMcd());
			tieptr->setTieTo(newCore, valueB->getType(), valueB->getSection(), rangeB, valueB->getMbsf(), valueB->getMcd());
			
			valueA  = tieptr->getTiedValue();
			//std::cout << "P/a) " << valueA->getMbsf() << " " << valueA->getMcd() << " " << valueA->getNumber() << std::endl;		
			valueB  = tieptr->getTieToValue();
			//std::cout << "P/b) " << valueB->getMbsf() << " " << valueB->getMcd() << " " << valueB->getNumber() << std::endl;			
	
	
			//newCore->addTie(tieptr);
			if(prevmcd != mcd)
			{
				tieptr->setConstrained(false);
			}

			if(tieptr->getTieToValue() == NULL || tieptr->getTiedValue() == NULL)
			{
				if(tieptr->getTiedValue() == NULL)
				{
					infoTied = tieptr->getInfoTied();
					cout << "[DEBUG/ERROR:READSPLICETABLE] Could not find value at TIED " << infoTied->m_coreptr->getName() << infoTied->m_coreptr->getNumber() << endl;
				} else 
				{
					infoTied = tieptr->getInfoTieTo();
					cout << "[DEBUG/ERROR:READSPLICETABLE] Could not find value at TIETO " << infoTied->m_coreptr->getName() << infoTied->m_coreptr->getNumber() << endl;
				}
				for(iter = temp_list.begin(); iter != temp_list.end(); iter++)
				{
					temp_tieptr = (Tie*) *iter;
					if(temp_tieptr == NULL) continue; 
					
					infoTied = temp_tieptr->getInfoTied();
					infoTied->m_coreptr->deleteTie(temp_tieptr->getId());
					delete temp_tieptr;
					temp_tieptr = NULL;
				}
				return -1;			
			}
		}

		tieptr->setAppend(appendflag, allflag);
		tieptr->setOrder(order);
		order++;
		token_num = 0;
	}
	
	dataptr->update();
	dataptr->update();

	temp_list.clear();

	return 1;
}

int ReadEqLogDepthTable( FILE *fptr, Data* dataptr, const char* affinefilename )
{
	if(dataptr == NULL) return 0;
	
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	// first line
	if(fgets(line, MAX_LINE, fptr) != NULL) 
	{
		getToken(line, token);	// Equivalent
		toupper(&token[0]);
		if(strcmp(token, "EQUIVALENT") == 0)
		{		
			getToken(line, token);	// Log
			getToken(line, token);	// Depth
			getToken(line, token);	// Table:
			
			getToken(line, token);	// Leg
			// check leg
			getToken(line, token);				
			if(strcmp(dataptr->getLeg(), token) !=0) return 0;
			
			getToken(line, token);	// Site
			// check site
			getToken(line, token);				
			if(strcmp(dataptr->getSite(), token) !=0) return 0;
		}
		token_num = 0;			
	}
	
	double stretch_value = 0.0;
	// second line
	if(fgets(line, MAX_LINE, fptr) != NULL) 
	{
		getToken(line, token);	// Overall
		toupper(&token[0]);
		if(strcmp(token, "OVERALL") == 0) 
		{
			getToken(line, token);	// Y or N
			toupper(&token[0]);
			if(token[0] == 'Y') 
			{
				//autocorr_status = YES;
				//did_log_mudline_adj = YES;
				dataptr->setCorrStatus(YES);
				
				getToken(line, token);	// MudlineOffset
				getToken(line, token);	
				dataptr->setMudLine(atof(token));

				getToken(line, token);	// Stretch/Compress
				getToken(line, token);	
				stretch_value = atof(token);
				dataptr->setStretch(stretch_value);
				
			} else 
			{
				//autocorr_status = NO;
				//did_log_mudline_adj = NO;
			}
		}
		token_num = 0;			
	}
	stretch_value *= 0.01;
	
		
	// third line
	int affine_status = NO;
	int already_applied_affine = NO;
	if(fgets(line, MAX_LINE, fptr) != NULL) 
	{
		getToken(line, token);	// Affine
		toupper(&token[0]);
		if(strcmp(token, "AFFINE") == 0) 
		{		
			getToken(line, token);	// Y or N
			toupper(&token[0]);
			if(token[0] == 'Y') 
			{
				// set affine status
				affine_status = YES;
				dataptr->setAffineStatus(YES);	
				// check current affine information
				getToken(line, token);
				// filename ............ todo........ what to do...... 
				if(affinefilename != NULL)
				{
					already_applied_affine = YES;
					if(strcmp(token, affinefilename) != 0)
					{
						//return 0;
#ifdef DEBUG						
						cout << "[ERROR] Affine Table File Name is different " << endl;
#endif
					}
				} 
			} else 
			{
				// set affine status
			}
		}
		token_num = 0;			
	}
		
	Hole* newHole = NULL;
	Core* newCore = NULL;

	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Tie* tieptr = NULL;
	char type;
	char section[2];
	memset(section, 0, 2);
	data_range range;
	double mbsf, mcd, rate, b;
	
	double depth_offset;
	char value_type = '*';
	int	ties_no;
	bool old_format = false;
	double eld;
	TieInfo* infoptr = NULL;	
	char hole_name[10];
	int ret;
	// from fourth...
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		// check hole name
		getToken(line, token);		// Hole
		
		toupper(&token[0]);
		if(strcmp(token, "HOLE") == 0) 
		{			
			getToken(line, token);		
			toupper(&token[0]);
			memset(hole_name, 0, 10);
			strcpy(hole_name, token);	
			newHole = dataptr->getHole(&hole_name[0]);
			if(newHole == NULL) 
			{
				token_num = 0;
				continue;
			}		

			// check core number
			getToken(line, token);		// Core
			getToken(line, token);	
			newCore = newHole->getCoreByNo(atoi(token));
			if(newCore == NULL)
			{
				token_num = 0;
				continue;
			}	
					
			if(affine_status == YES) 
			{
				getToken(line, token);		// AffineOffset		
				getToken(line, token);
				depth_offset = atof(token);
				
				getToken(line, token);		
				toupper(&token[0]);	
				if(already_applied_affine == NO)
				{
					if(token[0] == 'Y') 
					{ 
						newCore->setDepthOffset(depth_offset, value_type, true, true); // applied, fromfile
					} else if (token[0] == 'N')
					{
						newCore->setDepthOffset(depth_offset, value_type, false, true);
					}
				}
			} else 
			{
				getToken(line, token);		// AffineOffset		
				getToken(line, token);	
				getToken(line, token);			
			}
						
			// check tie number
			getToken(line, token);		// #Ties
			getToken(line, token);
			ties_no = atoi(token);
			token_num = 0;	
			infoptr = NULL;
			//if (ties_no > 0)
			//cout << "ties_no " << ties_no << " " <<  hole_name << newCore->getNumber() << endl;

			for(int i = 0; i < ties_no; i++) 
			{
				if(fgets(line, MAX_LINE, fptr)!=NULL)
				{	
					// check site
					getToken(line, token);				
					//cout << "token_num =" << token_num << endl;
					// 12 - > normal
					/*old_format = false;
					if (token_num < 12)
						old_format = true;*/
						
					if(strcmp(dataptr->getSite(), token) !=0) 
					{
						token_num = 0;
						continue;
					}
					
					// check hole name
					getToken(line, token);		
					toupper(&token[0]);
					memset(hole_name, 0, 10);
					strcpy(hole_name, token);
					holeptr = dataptr->getHole(&hole_name[0]);
					if(holeptr == NULL)
					{
						//cout << "2 out " << hole_name << endl;
						token_num = 0;
						continue;
					}
					
					// check core number
					getToken(line, token);	
					coreptr = holeptr->getCoreByNo(atoi(token));
					if(coreptr == NULL) 
					{
						token_num = 0;
						continue;
					}

					// type
					getToken(line, token);	
					toupper(&token[0]);	
					type = token[0];
					
					// section
					getToken(line, token);	
					toupper(&token[0]);
					strcpy(section, token);
					
					// top - bottom
					getToken(line, token);		
					range.top = atof(token);
					getToken(line, token);		
					range.bottom = atof(token);
					
					// mbsf
					getToken(line, token);		
					mbsf = atof(token);
				
					// need to check....
					// mcd ==> log depth
					getToken(line, token);		
					mcd = atof(token);

					/*if (old_format == false)
					{
						getToken(line, token);		
						eld = atof(token);
					}*/
									
					// rate
					getToken(line, token);		
					rate = atof(token);
				
					// b 
					getToken(line, token);		
					b = atof(token);
					
					//if (old_format == false)
					//{
					//eld = (mcd * stretch_value - b) * rate + b;
					//}
					//cout << "eld = " << eld << endl;
					//shift =  mcd - mcd * rate - b;
					//eld = mcd * rate + sihft;
					
					// create Tie and add
					// todo???????? 
					//cout << "newCore =  " << newCore->getName() << newCore->getNumber() << endl;
					ret = getToken(line, token);		
					toupper(&token[0]);

					tieptr = new Tie(coreptr, type, section, range, mbsf, mcd, SAGAN_FIXED_TIE, true);
					
					tieptr->setRateandB(rate, b);
					newCore->addTie(tieptr);
					infoptr = tieptr->getInfoTied();
	
					//infoptr->m_eld = eld;
					if(strcmp(token, "S") == 0)
					{
						tieptr->setSharedFlag(true);
					} else 
					{
						tieptr->setSharedFlag(false);
					}
					if(ret > 0)
					{
						getToken(line, token);		
						eld = atof(token);
						infoptr->m_eld = eld;
						//cout << " get eld " << eld << endl;
					} else 
					{
						infoptr->m_eld = mcd;
					}
		
				} // end of if statement
			} // end of for statement
			
		} // end of if statement
		
		token_num = 0;			
	} // end of while statement

	return 1;
}

int ReadStrat( FILE *fptr, Data* dataptr, int datatype )
{
	if(dataptr == NULL) return 0;

	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	Hole* newHole = NULL;
	Core* newCore = NULL;
	Core* coreptr = NULL;
	Strat* stratptr = NULL;

	char type, typeB;
	char section[2];
	char sectionB[2];
	memset(section, 0, 2);
	memset(sectionB, 0, 2);	
	double mbsf, mbsfB, interval, intervalB;
	
	char name[25];
	memset(name, 0, 25);
	char code[25];
	memset(code, 0, 25);
	double age[2];
	
	int numOfType = 0;
	char holeA[10];
	memset(holeA, 0, 10);
	char holeB[10];
	memset(holeB, 0, 10);
	int coreA, coreB;
	
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		// name
		getToken(line, token);								
		strcpy(name, token);
		
		// code
		getToken(line, token);				
		strcpy(code, token);
		
		// age
		getToken(line, token);				
		age[0] = atof(token);
		getToken(line, token);				
		age[1] = atof(token);

		// leg, site, hole, core
		// check leg
		getToken(line, token);				
		if(strcmp(dataptr->getLeg(), token) !=0) 
		{
			token_num = 0;
			continue;
		}	
		
		// check site
		getToken(line, token);				
		if(strcmp(dataptr->getSite(), token) !=0) 
		{
			token_num = 0;
			continue;
		}
		
		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		memset(holeA, 0, 10);
		strcpy(holeA, token);
		//cout << "holeA = " << holeA << endl;

		// check core number
		getToken(line, token);	
		coreA = atoi(token);

		// type, section, interval, mbsf
		// type
		getToken(line, token);	
		toupper(&token[0]);	
		type = token[0];
		
		// section
		getToken(line, token);	
		toupper(&token[0]);
		strcpy(section, token);

		// interval
		getToken(line, token);		
		interval = atof(token);
		
		// mbsf
		getToken(line, token);		
		mbsf = atof(token);

		// check leg
		getToken(line, token);				
		if(strcmp(dataptr->getLeg(), token) !=0) 
		{
			token_num = 0;
			continue;
		}	
		
		// check site
		getToken(line, token);				
		if(strcmp(dataptr->getSite(), token) !=0)
		{
			token_num = 0;
			continue;
		}	
			
		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		memset(holeB, 0, 10);
		strcpy(holeB, token);
		//cout << "holeB = " << holeB << endl;

		// check core number
		getToken(line, token);	
		coreB = atoi(token);

		// type, section, interval, mbsf
		// type
		getToken(line, token);	
		toupper(&token[0]);	
		typeB = token[0];
		
		// section
		getToken(line, token);	
		toupper(&token[0]);
		strcpy(sectionB, token);

		// interval
		getToken(line, token);		
		intervalB = atof(token);
		
		// mbsf
		getToken(line, token);		
		mbsfB = atof(token);
		//cout << "bottom msbf " << mbsf << endl;
		

		numOfType = dataptr->getNumOfTypes();
		//cout << "num of type = " << numOfType << endl;
		for(int i = 0; i < numOfType; i++)
		{
			// create Strat and add
			stratptr = new Strat(name, code, age[0], age[1]);
			//cout << " strat is created : "<< name << " " << code << " " << newCore->getName() << newCore->getNumber() << endl;
			//cout << "top msbf " << mbsf << endl;
			//cout << " i = " << i << endl;
			newHole = dataptr->getHole(holeA, i);
			if(newHole == NULL)
			{
				//cout << "A out " << holeA << endl;
				delete stratptr;
				token_num = 0;
				continue;
			}
			newCore = newHole->getCoreByNo(coreA);
			if(newCore == NULL) 
			{;
				delete stratptr;
				token_num = 0;
				continue;
			}
			coreptr = newCore;		
			
			newHole = dataptr->getHole(holeB, i);
			if(newHole == NULL)  
			{
				//cout << "B out " << holeB << endl;
				delete stratptr;
				token_num = 0;
				continue;
			}
			newCore = newHole->getCoreByNo(coreB);
			if(newCore == NULL)
			{
				delete stratptr;
				token_num = 0;
				continue;
			}						
			//cout << "found all " << endl;
			
			stratptr->setTopCoreId(coreptr->getId());
			stratptr->setBotCoreId(newCore->getId());
			stratptr->setTopType(type);
			stratptr->setTopSection(&section[0]);
			stratptr->setTopInterval(interval);		
			stratptr->setTopMbsf(mbsf);
			stratptr->setDataType(datatype);
			stratptr->setTopCore(coreptr);

			stratptr->setBotType(typeB);
			stratptr->setBotSection(&sectionB[0]);
			stratptr->setBotInterval(intervalB);		
			stratptr->setBotMbsf(mbsfB);
			stratptr->setBotCore(newCore);

			coreptr->addStrat(stratptr);	

			if(newCore->getId() != coreptr->getId())
			{
				//newCore->addStrat(stratptr);	
			}
		}
		
		token_num = 0;	
	}
	if(stratptr == NULL) return 0;
	//cout << "strat order " <<  order << endl;	
	return 1;
}

int ReadStratTable( FILE *fptr, Data* dataptr )
{
	if(dataptr == NULL) return 0;

	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	Hole* newHole = NULL;
	Core* newCore = NULL;
	Core* coreptr = NULL;
	Strat* stratptr = NULL;

	char type, typeB;
	char section[2];
	memset(section, 0, 2);
	char sectionB[2];
	memset(sectionB, 0, 2);
	double mbsf, interval, mbsfB, intervalB;
	
	char name[25];
	memset(name, 0, 25);
	char code[25];
	memset(code, 0, 25);
	double age[2];
	int order =0;
	int datatype;
	
	int numOfType = 0;
	char holeA[10];
	char holeB[10];
	int coreA, coreB;	
	
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		// name
		getToken(line, token);			
		if(token[0] == '#')
		{
			token_num = 0;
			continue;
		}
		strcpy(name, token);
		
		// code
		getToken(line, token);				
		strcpy(code, token);
		
		// datatype
		getToken(line, token);	
		datatype = atoi(token);		
		
		// age
		getToken(line, token);				
		age[0] = atof(token);
		getToken(line, token);				
		age[1] = atof(token);

		// leg, site, hole, core
		// check leg
		getToken(line, token);				
		if(strcmp(dataptr->getLeg(), token) !=0) 
		{
			token_num = 0;
			continue;
		}	
		
		// check site
		getToken(line, token);				
		if(strcmp(dataptr->getSite(), token) !=0) 
		{
			token_num = 0;
			continue;
		}
		
		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		memset(holeA, 0, 10);
		strcpy(holeA, token);

		// check core number
		getToken(line, token);	
		coreA = atoi(token);

		// type, section, interval, mbsf
		// type
		getToken(line, token);	
		toupper(&token[0]);	
		type = token[0];
		
		// section
		getToken(line, token);	
		toupper(&token[0]);
		strcpy(section, token);

		// interval
		getToken(line, token);		
		interval = atof(token);
		
		// mbsf
		getToken(line, token);		
		mbsf = atof(token);

		// check leg
		getToken(line, token);				
		if(strcmp(dataptr->getLeg(), token) !=0) 
		{
			token_num = 0;
			continue;
		}	
		
		// check site
		getToken(line, token);				
		if(strcmp(dataptr->getSite(), token) !=0)
		{
			token_num = 0;
			continue;
		}	
			
		// check hole name
		getToken(line, token);		
		toupper(&token[0]);
		memset(holeB, 0, 10);
		strcpy(holeB, token);
		
		// check core number
		getToken(line, token);	
		coreB = atoi(token);
				
		// type, section, interval, mbsf
		// type
		getToken(line, token);	
		toupper(&token[0]);	
		typeB = token[0];
		
		// section
		getToken(line, token);	
		toupper(&token[0]);
		strcpy(sectionB, token);

		// interval
		getToken(line, token);		
		intervalB = atof(token);
		
		// mbsf
		getToken(line, token);		
		mbsfB = atof(token);
		//cout << "bottom msbf " << mbsf << endl;
				


		numOfType = dataptr->getNumOfTypes();
		//cout << "num of type = " << numOfType << endl;
		for(int i = 0; i < numOfType; i++)
		{
			// create Strat and add
			stratptr = new Strat(name, code, age[0], age[1]);
			//cout << " strat is created : "<< name << " " << code << " " << newCore->getName() << newCore->getNumber() << endl;
			//cout << "top msbf " << mbsf << endl;
			newHole = dataptr->getHole(holeA, i);
			if(newHole == NULL)
			{
				//cout << "out " <<holeA << endl;
				delete stratptr;
				token_num = 0;
				continue;
			}
			newCore = newHole->getCoreByNo(coreA);
			if(newCore == NULL) 
			{
				delete stratptr;
				token_num = 0;
				continue;
			}
			coreptr = newCore;		
			
			newHole = dataptr->getHole(holeB, i);
			if(newHole == NULL)  
			{
				//cout << "out " << holeB << endl;
				delete stratptr;
				token_num = 0;
				continue;
			}
			newCore = newHole->getCoreByNo(coreB);
			if(newCore == NULL)
			{
				delete stratptr;
				token_num = 0;
				continue;
			}						
			
			stratptr->setTopCoreId(coreptr->getId());
			stratptr->setBotCoreId(newCore->getId());
			stratptr->setTopType(type);
			stratptr->setTopSection(&section[0]);
			stratptr->setTopInterval(interval);		
			stratptr->setTopMbsf(mbsf);
			stratptr->setDataType(datatype);
			stratptr->setTopCore(coreptr);
			stratptr->setOrder(order);

			stratptr->setBotType(typeB);
			stratptr->setBotSection(&sectionB[0]);
			stratptr->setBotInterval(intervalB);		
			stratptr->setBotMbsf(mbsfB);
			stratptr->setBotCore(newCore);

			coreptr->addStrat(stratptr);	

			if(newCore->getId() != coreptr->getId())
			{
				//newCore->addStrat(stratptr);	
			}
		}

		order++;
		token_num = 0;	
	}
	if(stratptr == NULL) return 0;
	
	//cout << "strat order " <<  order << endl;
	return 1;
}

int ReadCullTable( FILE *fptr, int coretype, Data* dataptr, char* annotation )
{
	if(dataptr == NULL) return 0;
	
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);

	Hole* newHole = NULL;
	Core* newCore = NULL;
	Value* newValue = NULL;
	char* holename = NULL;
	string prev_holename = "";
	char* prev_hole_ptr;
	int coreid = -1;
	int prev_coreid = -1;	
	double top = -1;
	int section_id = -1;
	int quality;
	int count = 0;
			
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		// 154 	926 	A 	1 	H 	1 	4.70 	4.70 
		// leg
		getToken(line, token);
		if(token[0] == '#') 
		{
			//cout << "line " << line << endl;
			token_num = 0;
			continue;
		}

		// site
		getToken(line, token);
		
		// hole
		getToken(line, token);
		holename = &token[0];
		prev_hole_ptr = (char*) prev_holename.c_str();
		if(strcmp(holename, prev_hole_ptr) != 0)
		{
			// find hole with type/annotation
			//cout << "hole name = " << holename << endl;
			newHole = dataptr->getHole(holename, coretype, annotation);
			if(newHole == NULL) 
			{
#ifdef DEBUG			
				cout << "[ERROR] DataParser/CullTable: could not find hole " << endl;
#endif
				token_num = 0;
				//return 0;
				continue;
			}	
			prev_coreid = -1;
		}
		prev_holename = holename;
		
		// core
		getToken(line, token);
		coreid = atoi(token);
		if(coreid != prev_coreid)
		{
			newCore = newHole->getCoreByNo(coreid);
			if(newCore == NULL)
			{
#ifdef DEBUG
				cout << "[ERROR] DataParser/CullTable: could not find core " << holename << coreid << endl;
#endif
				token_num = 0;
				continue;
				//return 0;
			}
			prev_coreid = coreid;
		}

		// section type or badcore
		getToken(line, token);
		if (strcmp(token, "badcore") ==0)
		{
			// I think that it has to be changed...
			newCore->setQuality(BAD_CULLTABLE);
			token_num = 0;
#ifdef DEBUG			
			cout << "[ERROR] DataParser/CullTable: Bad core " << endl;
#endif
			continue;
		}
		// section id
		getToken(line, token);
		section_id = atoi(token);

		// top
		getToken(line, token);
		top = atof(token);
		
		newValue = newCore->getValue(section_id, top);
		if(newValue != NULL)
		{
			newValue->setQuality(BAD_CULLTABLE);
			count ++;
		}	
		token_num = 0;
	}
	
#ifdef DEBUG	
	cout << "[DEBUG] " << count << " values are culled" << endl;
#endif	
	dataptr->update();
	dataptr->update();
	
	return 1;
}

int ReadLog( FILE *fptr, char* label, Data* dataptr, int selectedColumn, string& result )
{
	if(dataptr == NULL) return 0;

	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);

	Hole* newHole = NULL;
	Core* newCore = NULL;
	Value* newValue = NULL;
	int value_index =0;
		
	int length=0;
	data_range range;
	
	fgets(line, MAX_LINE, fptr);
	fgets(line, MAX_LINE, fptr);
	if(fgets(line, MAX_LINE, fptr) != NULL) 
	{
		getToken(line, token);	
		getToken(line, token);				
		toupper(&token[0]);
		if(strcmp(token, "SITE") == 0) 
		{
			getToken(line, token);
			//cout << "site= " << token << endl;	
			dataptr->setSite(token);	
								
		}
		token_num = 0;	
	}
	if(fgets(line, MAX_LINE, fptr) != NULL) 
	{		
		getToken(line, token);
		getToken(line, token);		
		toupper(&token[0]);
		if(strcmp(token, "LEG") == 0) 
		{
			getToken(line, token);	
			//cout << "leg= " << token << endl;
			dataptr->setLeg(token);
		}	
		token_num = 0;	
	}
	if(fgets(line, MAX_LINE, fptr) != NULL) 
	{
		getToken(line, token);	
		getToken(line, token);	
		toupper(&token[0]);
		if(strcmp(token, "HOLE") == 0) 
		{		
			getToken(line, token);	

			// HOLE_NUMBER
			newHole = dataptr->createHole(0, &token[0], LOGTYPE);
			//newHole->setType(LOGTYPE);
			if(newHole == NULL) return 0;
			//newHole->setType(LOGTYPE);
			newCore = newHole->createCore(0);
			newCore->setNumber(0);	
			//newCore->setType(LOGTYPE);	
			if(newCore == NULL) return 0;
		}		
		token_num = 0;		
	}
	if(newHole == NULL) return 0;	
	
	double fvalue=0;
	value_index = 0;
	// read column ids......
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{
		getToken(line, token);
		if (strlen(token) == 1) 
		{
			token_num = 0;
			continue;
		}
		
		newValue = newCore->createValue(value_index);
		//newValue->setType(token[0]);
		if(newValue == NULL) return 0;
								
		newValue->setDepth(atof(token));
		newValue->setMbsf(atof(token));
		newValue->setELD(atof(token));
		value_index++;
		
		getToken(line, token);	
		fvalue = atof(token);
		newValue->setRawData(fvalue);
		//newValue->setRange(range);
		token_num = 0;
	} // end of while
	return 1;
}

int WriteIODPAffineTable(FILE *fptr, Data *dataptr)
{
	if (dataptr == NULL)
		return 0;

	// 154	926	A	1	H	0.00	N
	// leg site hole# Core# type depth applied-or-not
	const char* leg = dataptr->getLeg();
	const char* site = dataptr->getSite();

	fprintf (fptr, "# Site, Hole, Core, Core Type, Depth CSF (m), Depth CCSF (m), Cumulative Offset (m), Differential Offset (m), Growth Rate, Shift Type, Data Used, Quality Comment\n");
	fprintf (fptr, "# Generated By Correlator\n");
	std::vector<char*> holeNames;

	const int holesize = dataptr->getNumOfHoles();
	for (int i=0; i < holesize; i++)
	{
		// ensure we don't write the same hole's cores twice in cases
		// where multiple data types are loaded
		Hole *holeptr = dataptr->getHole(i);
		char *holename = (char*) holeptr->getName();
		bool holeWritten = false;
		for (int nameIdx=0; nameIdx < holeNames.size(); nameIdx++)
		{
			if (strcmp(holeNames[nameIdx],holename) == 0)
			{
				holeWritten = true;
				break;
			}
		}
		if (holeWritten == true) continue;
		holeNames.push_back(holename);

		// write hole
		double cumOffset = 0.0;
		const int coresize = holeptr->getNumOfCores();
		for (int coreIdx=0; coreIdx < coresize; coreIdx++)
		{
			Core *coreptr = holeptr->getCore(coreIdx);
			if (coreptr == NULL) continue;
			const int coreno = coreptr->getNumber();

			Value *valueptr = coreptr->getValue(0);
			if (!valueptr) {
				//cout << "core " << holename << coreptr->getNumber() << " has no values, skipping" << endl;
				continue;
			}
			const char coretype = (valueptr != NULL ? valueptr->getType() : 'X');
			const double depthOffset = coreptr->getDepthOffset();
			const double coreTop = valueptr->getDepth();
			const double shiftedTop = coreTop + depthOffset;
			const double diffOffset = cumOffset - depthOffset;
			cumOffset += depthOffset;
			const double growthRate = (coreIdx == 0 ? 0.0 : shiftedTop / coreTop);
			string shiftType = AFFINE_TIE_STR;
			if (coreTop == 0.0 && diffOffset == 0.0)
				shiftType = AFFINE_ANCHOR_STR;
			if (coreptr->getAffineType() == AFFINE_SET)
				shiftType = AFFINE_SET_STR;
			string dataType = coreptr->getAffineDatatype();
			string comment = coreptr->getComment();

#ifdef NEWOUTPUT
			string dataLine;
			const string format("ssicfffffsss");
			makeDelimString(format, dataLine, site, holename, coreno, coretype, coreTop, shiftedTop, cumOffset, depthOffset, growthRate, shiftType.c_str(), dataType.c_str(), comment.c_str());
			dataLine += '\n';
			fprintf(fptr, "%s", dataLine.c_str());
#else
			//fprintf (fptr, "%s \t%s \t%c \t%d \t%c \t%f \t%c \t\t%f \t%f\n", leg, site, holename, coreno, coretype, depthoffset, status, range->mindepth, range->maxdepth);
			fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%f \t%c\n", leg, site, holename, coreno, coretype, depthOffset, status);
#endif // NEWOUTPUT
			//prev_depthoffset = depthoffset;
		}
	}

	return 1;
}

int WriteAffineTable( FILE *fptr, Data* dataptr )
{
	if(dataptr == NULL) return 0;

	// 154	926	A	1	H	0.00	N
	// leg site hole# Core# type depth applied-or-not
	const char* leg = dataptr->getLeg();
	const char* site = dataptr->getSite();

	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	int holesize = dataptr->getNumOfHoles();
	char* holename = NULL;
	int coresize=0;
	int coreno =0;
	char coretype=' ';
	double depthoffset=0.0f;
	char status='N';

	data_range*	range;
	
	fprintf (fptr, "# Leg, Site, Hole, Core No, Section Type, Depth Offset, Y/N \n");
	fprintf (fptr, "# Generated By Correlator\n");
	std::vector<char*> hole_names;	
	bool registered_flag = false;
	double prev_depthoffset =999.0f;
								
	for(int i=0; i < holesize; i++)
	{
		holeptr = dataptr->getHole(i);
		//if(holeptr == NULL) continue;
		holename = (char*) holeptr->getName();
		
		registered_flag = false;
		for(int k=0; k < hole_names.size(); k++)
		{
			if (strcmp(hole_names[k],holename) == 0)
			{
				registered_flag = true;
				break;
			}	
		}
		if(registered_flag == true) continue;
		hole_names.push_back(holename);

		coresize = holeptr->getNumOfCores();
		for(int j=0; j < coresize; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			coreno = coreptr->getNumber();
			
			valueptr = coreptr->getValue(0);
			range = coreptr->getRange();
			if(valueptr == NULL) 
				coretype = 'X';
			else 
				coretype = valueptr->getType();
			depthoffset = coreptr->getDepthOffset();
			
			if(coreptr->getAffineStatus() == 1)
			{	
				if(coreptr->getAffineType() == 1)
					status = 'Y';
				else 
				{
					if(prev_depthoffset != depthoffset)
					{
						status = 'Y';
					} else 
						status = 'N';
				}
			} else 
				status = 'N';
#ifdef NEWOUTPUT
			// brgbrg
			string dataLine;
			const string format("sssicfc");
			makeDelimString(format, dataLine, leg, site, holename, coreno, coretype, depthoffset, status);
			dataLine += '\n';
			fprintf(fptr, "%s", dataLine.c_str());
#else
			//fprintf (fptr, "%s \t%s \t%c \t%d \t%c \t%f \t%c \t\t%f \t%f\n", leg, site, holename, coreno, coretype, depthoffset, status, range->mindepth, range->maxdepth);
			fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%f \t%c\n", leg, site, holename, coreno, coretype, depthoffset, status);
#endif // NEWOUTPUT
			prev_depthoffset = depthoffset;
		}
	}
		
	return 1;
}

int WriteSpliceTable( FILE *fptr, Data* dataptr, const char* affinefilename)
{
	cout << "WriteSpliceTable!" << endl;

	if(dataptr == NULL) return 0;


	// 926	B	1	H	4	25.6	25.6	4.76	4.76	tie	
	// 926	C	1	H	2	57.5	57.5	2.58	4.76
	// site hole# core# type section top bottom mbsf mcd
	const char* site = dataptr->getSite();

	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	Tie* tieptr = NULL;
	int coresize =0;
	int tiesize =0;
	TieInfo* tieInfoptr = NULL;

	fprintf (fptr, "# Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd, TIE/APPEND, Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd\n");
	if(affinefilename == NULL)
		fprintf (fptr, "# AffineTable None\n");
	else 
		fprintf (fptr, "# AffineTable %s\n", affinefilename);	
	
	fprintf (fptr, "# Generated By Correlator\n");

	// how many real-tie
    int numHoles = dataptr->getNumOfHoles();
    int numCores, numTies;
    int count=0;
    for(int i=0; i < numHoles; i++)
    {
    	holeptr = dataptr->getHole(i);
    	if (holeptr == NULL) continue;
    	numCores =  holeptr->getNumOfCores();
    	for(int j=0; j < numCores; j++)
    	{
    		coreptr = holeptr->getCore(j);
    		if (coreptr == NULL) continue;
    		numTies = coreptr->getNumOfTies();
    		for(int k=0; k < numTies; k++)
    		{
    			tieptr = coreptr->getTie(k);
    			if (tieptr->getType() == REAL_TIE)
    			{
    				count++;
    			}
    		}
    	}
    }
	if (count == 0) return 0;

	int last_value_idx = 0;
	Value* first_value = NULL;
	Value* temp_value = NULL;
	char* value_section = NULL;
	
  	for(int i=0; i < count; i++)
  	{
  		tieptr = findTie(dataptr, i);

		if(tieptr->getSharedFlag() == false)
		{
			tieInfoptr = tieptr->getInfoTied();
			if(tieInfoptr == NULL) continue;
			if(tieInfoptr->m_coreptr == NULL) continue;
			if(tieptr->isAppend() == false) 
			{
				temp_value = tieInfoptr->m_valueptr;
				if(temp_value == NULL) continue;

#ifdef NEWOUTPUT
				string dataLine;
				const string format("ssiccffffs");
				makeDelimString(format, dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
				                tieInfoptr->m_valuetype, tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
				                temp_value->getMbsf(), temp_value->getMcd(), "TIE");
				dataLine += delimiter;
				// brgtodo 9/8/2014 end with delimiter or not?
				fprintf(fptr, "%s", dataLine.c_str());
#else
				fprintf (fptr, "%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f \tTIE",
					site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
					tieInfoptr->m_valuetype,
					//tieInfoptr->m_section[0], tieInfoptr->m_top, tieInfoptr->m_bottom, 
					tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
					temp_value->getMbsf(), temp_value->getMcd());
					//tieInfoptr->m_mbsf, tieInfoptr->m_mcd);
#endif // NEWOUTPUT

				tieInfoptr = tieptr->getInfoTieTo();
				if(tieInfoptr == NULL) continue;
				if(tieInfoptr->m_coreptr == NULL) continue;
				temp_value = tieInfoptr->m_valueptr;
				if(temp_value == NULL) continue;

#ifdef NEWOUTPUT
				// brgbrg New Way Yay!
				dataLine.clear();
				//const string delim(" \t");
				//const string format("ssiccffff");
				makeDelimString("ssiccffff", dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(),
				                tieInfoptr->m_valuetype, tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
				                temp_value->getMbsf(), temp_value->getMcd());
				dataLine += '\n';
				fprintf(fptr, "%s", dataLine.c_str());
#else
				fprintf (fptr, " \t%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f\n",
					site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
					tieInfoptr->m_valuetype,
					//tieInfoptr->m_section[0], tieInfoptr->m_top, tieInfoptr->m_bottom, 
					tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
					temp_value->getMbsf(), temp_value->getMcd());					
					//tieInfoptr->m_mbsf, tieInfoptr->m_mcd);
#endif // NEWOUTPUT
			} else 
			{
				if(tieptr->isAll() == false)
				{
					if (tieInfoptr->m_valueptr != NULL)
					{
						temp_value = tieInfoptr->m_valueptr;

#ifdef NEWOUTPUT
						// brgbrg New Way Yay!
						string dataLine;
						const string format("ssiccffffs");
						makeDelimString(format, dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
						                tieInfoptr->m_valuetype, tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
						                temp_value->getMbsf(), temp_value->getMcd(), "APPEND");
						dataLine += delimiter;
						fprintf(fptr, "%s", dataLine.c_str());
#else
						fprintf (fptr, "%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f \tAPPEND",
						site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
						tieInfoptr->m_valuetype,
						//tieInfoptr->m_section[0], tieInfoptr->m_top, tieInfoptr->m_bottom, 
						tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
						temp_value->getMbsf(), temp_value->getMcd());
#endif // NEWOUTPUT
					} else 
					{
						last_value_idx = tieInfoptr->m_coreptr->getNumOfValues() -1;
						first_value = tieInfoptr->m_coreptr->getValue(last_value_idx);
						if (first_value != NULL)
						{
							value_section = first_value->getSection();

#ifdef NEWOUTPUT
							// brgbrg New Way Yay!
							string dataLine;
							const string format("ssiccffffs");
							makeDelimString(format, dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
							                first_value->getType(), value_section[0], first_value->getTop(), first_value->getBottom(), 
							                first_value->getMbsf(), first_value->getMcd(), "APPEND");
							dataLine += delimiter;
							fprintf(fptr, "%s", dataLine.c_str());
#else
							fprintf (fptr, "%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f \tAPPEND",
							site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
							first_value->getType(),
							value_section[0], first_value->getTop(), first_value->getBottom(), 
							first_value->getMbsf(), first_value->getMcd());
#endif // NEWOUTPUT
						}
					}
					tieInfoptr = tieptr->getInfoTieTo();
					if(tieInfoptr == NULL) continue;
					if(tieInfoptr->m_coreptr == NULL) continue;
					
					if (tieInfoptr->m_valueptr != NULL) 
					{
						temp_value = tieInfoptr->m_valueptr;
#ifdef NEWOUTPUT
						string dataLine;
						const string format("ssiccffff");
						makeDelimString(format, dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
						                tieInfoptr->m_valuetype, tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
						                temp_value->getMbsf(), temp_value->getMcd());
						dataLine += "\n";
						fprintf(fptr, "%s", dataLine.c_str());
#else

						fprintf (fptr, " \t%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f\n",
						site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
						tieInfoptr->m_valuetype,
						//tieInfoptr->m_section[0], tieInfoptr->m_top, tieInfoptr->m_bottom, 
						tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
						temp_value->getMbsf(), temp_value->getMcd());
#endif // NEWOUTPUT
					} else 
					{
						first_value = tieInfoptr->m_coreptr->getValue(0);
						if(first_value != NULL)
						{
							value_section = first_value->getSection();

#ifdef NEWOUTPUT
							string dataLine;
							const string format("ssiccffff");
							makeDelimString(format, dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
							                first_value->getType(),	value_section[0], first_value->getTop(), first_value->getBottom(), 
							                first_value->getMbsf(), first_value->getMcd());
							dataLine += "\n";
							fprintf(fptr, "%s", dataLine.c_str());
#else
							fprintf (fptr, " \t%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f\n",
							site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
							first_value->getType(),
							value_section[0], first_value->getTop(), first_value->getBottom(), 
							first_value->getMbsf(), first_value->getMcd());
#endif // NEWOUTPUT
						}
					}
				} else // tieptr->isAll == true
				{
					temp_value = tieInfoptr->m_valueptr;
					if(temp_value == NULL) continue;

#ifdef NEWOUTPUT
					string dataLine;
					const string format("ssiccffffs");
					makeDelimString(format, dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
					                tieInfoptr->m_valuetype, tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
					                temp_value->getMbsf(), temp_value->getMcd(), "TIE");
					dataLine += delimiter;
					fprintf(fptr, "%s", dataLine.c_str());
#else
					fprintf (fptr, "%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f \tTIE",
					site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
					tieInfoptr->m_valuetype,
					//tieInfoptr->m_section[0], tieInfoptr->m_top, tieInfoptr->m_bottom, 
					tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
					temp_value->getMbsf(), temp_value->getMcd());
					//tieInfoptr->m_mbsf, tieInfoptr->m_mcd);
#endif // NEWOUTPUT

					tieInfoptr = tieptr->getInfoTieTo();
					if(tieInfoptr == NULL) continue;
					if(tieInfoptr->m_coreptr == NULL) continue;
					temp_value = tieInfoptr->m_valueptr;
					if(temp_value == NULL) continue;
					
#ifdef NEWOUTPUT
					dataLine.clear();
					makeDelimString("ssiccffff", dataLine, site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
					                tieInfoptr->m_valuetype, tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
					                temp_value->getMbsf(), temp_value->getMcd());
					dataLine += "\n";
					fprintf(fptr, "%s", dataLine.c_str());
#else
					fprintf (fptr, " \t%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f\n",
					site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
					tieInfoptr->m_valuetype,
					//tieInfoptr->m_section[0], tieInfoptr->m_top, tieInfoptr->m_bottom, 
					tieInfoptr->m_section[0], temp_value->getTop(), temp_value->getBottom(), 
					temp_value->getMbsf(), temp_value->getMcd());
					//tieInfoptr->m_mbsf, tieInfoptr->m_mcd);
#endif // NEWOUTPUT

					last_value_idx = tieInfoptr->m_coreptr->getNumOfValues() -1;
					first_value = tieInfoptr->m_coreptr->getValue(last_value_idx);
					if (first_value != NULL)
					{
						value_section = first_value->getSection();

#ifdef NEWOUTPUT
						dataLine.clear();
						makeDelimString("ssiccffffs", dataLine, site, tieInfoptr->m_coreptr->getName(),
						                tieInfoptr->m_coreptr->getNumber(), first_value->getType(),	value_section[0], first_value->getTop(),
						                first_value->getBottom(), first_value->getMbsf(), first_value->getMcd(), "APPEND");
						dataLine += "\n";
						fprintf(fptr, "%s", dataLine.c_str());
#else
						fprintf (fptr, "%s \t%s \t%d \t%c \t%c \t%f \t%f \t%f \t%f \tAPPEND\n",
						site, tieInfoptr->m_coreptr->getName(), tieInfoptr->m_coreptr->getNumber(), 
						first_value->getType(),
						value_section[0], first_value->getTop(), first_value->getBottom(), 
						first_value->getMbsf(), first_value->getMcd());
#endif // NEWOUTPUT
					}
				}
			}
		}
	}

	return 1;
}


Tie* findTie( Data* dataptr, int order )
{
	int numHoles = dataptr->getNumOfHoles();
	int numCores, numTies;

	Hole* holeptr;
	Core* coreptr;
	Tie* tieptr;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = dataptr->getHole(i);
		if (holeptr == NULL) continue;
		numCores =  holeptr->getNumOfCores();
		for(int j=0; j < numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if (coreptr == NULL) continue;
			numTies = coreptr->getNumOfTies();
			for(int k=0; k < numTies; k++)
			{
				tieptr = coreptr->getTie(k);
				if (tieptr->getType() == REAL_TIE && tieptr->getOrder() == order)
				{
					return tieptr;
				}
			}
		}
	}
	return NULL;
}

int WriteEqLogDepthTable( FILE *fptr, Data* dataptr, const char* affinefilename )
{
	if(dataptr == NULL) return 0;

	//fprintf (fptr, "# Leg, Site, Hole, Core No, AffineOffset, Depth Offset, Y/N #Ties Eld Ties No \n");
	//fprintf (fptr, "# Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd, Eld, a, b, S\n");
	//fprintf (fptr, "# Generated By Correlator\n");

	const char* leg = dataptr->getLeg();
	const char* site = dataptr->getSite();
	// Equivalent Log Depth Table:  Leg 162  Site 984
	fprintf (fptr, "Equivalent Log Depth Table: \tLeg \t%s \tSite \t%s\n", leg, site);
	
	// Overall  Y  MudlineOffset 0.30  Stretch/Compress 93.50
	double mudlineoffset = dataptr->getMudLine();
	double stretch = dataptr->getStretch();
	fprintf (fptr, "Overall \tY \tMudlineOffset \t%f \tStretch/Compress \t%f\n", mudlineoffset, stretch);
	
	// Affine Y     /home/ibex/sagan/sagan_testdata/leg162testdata/984.affine.pdem
	if (affinefilename == NULL)
		fprintf (fptr, "Affine \tN \t\n");
	else if (strlen(affinefilename) > 0)
		fprintf (fptr, "Affine \tY \t%s\n", affinefilename);
	else 
		fprintf (fptr, "Affine \tN\n");
		
	//Hole	A	Core	1	AffineOffset	0.00	N	#Ties	0
	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	int holesize = dataptr->getNumOfHoles();
	char* holename = NULL;
	int coresize=0;
	int coreno =0;
	char coretype=' ';
	double depthoffset=0;
	char status='N';
	int saganTies =0;
	
	Tie* tieptr = NULL;	
	TieInfo* infoTied = NULL;
	TieInfo* infoTieTo = NULL;
	Value* valueTied = NULL;	
	double mcd, eld;
  		
	for(int i=0; i < holesize; i++)
	{
		holeptr = dataptr->getHole(i);
		//if(holeptr == NULL) continue;
		holename = (char*) holeptr->getName();
		coresize = holeptr->getNumOfCores();
		for(int j=0; j < coresize; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			coreno = coreptr->getNumber();
			valueptr = coreptr->getValue(0);
			if(valueptr == NULL) continue;
			coretype = valueptr->getType();
			depthoffset = coreptr->getRawDepthOffset();
			if(coreptr->getRawAffineStatus() == 1)
				status = 'Y';
			else 
				status = 'N';

			saganTies = coreptr->getNumOfTies(SAGAN_TIE);
 
			fprintf (fptr, "Hole \t%s \tCore \t%d \tAffineOffset \t%f \t%c \t#Ties \t%d\n", holename, coreno, depthoffset, status, saganTies);
			// site hole core# type section top bottom mbsf mcd rate b S
			for(int k=0; k < saganTies; k++)
			{
				tieptr = coreptr->getTie(SAGAN_TIE, k);
				
				if(tieptr == NULL) continue;
				infoTied = tieptr->getInfoTied();
				if(infoTied == NULL) continue; 
				infoTieTo = tieptr->getInfoTieTo();
				valueTied = infoTied->m_valueptr;	
				if(valueTied == NULL) continue; 
				//mcd = valueTied->getMbsf() + depthoffset;
				mcd = infoTied->m_mcd;
				eld = infoTieTo->m_mcd;
				if(tieptr->getSharedFlag() == true)
					status = 'S';
				else 
					status = 'N';
					

				//fprintf (fptr, "%s \t%s \t%d \t%c \t%s \t%.4f \t%.4f \t%.4f \t%.4f \t%.4f \t%.4f \t%c \t%.5f\n", site, holename, coreno, valueTied->getType(), valueTied->getSection(),
				//				valueTied->getTop(), valueTied->getBottom(), valueTied->getMbsf(), mcd, 
				//				tieptr->getRate(), tieptr->getB(), status, valueTied->getELD());	
				fprintf (fptr, "%s \t%s \t%d \t%c \t%s \t%f \t%f \t%f \t%f \t%f \t%f \t%c \t%f\n", site, holename, coreno, valueTied->getType(), valueTied->getSection(),
								valueTied->getTop(), valueTied->getBottom(), valueTied->getMbsf(), valueTied->getMcd(), 
								tieptr->getRate(), tieptr->getB(), status, eld);
			}
		}
	}
	return 1;
}

Strat* findStrat( Data* dataptr, int order )
{
	int numHoles = dataptr->getNumOfHoles();
	int numCores, numStrats;

	Hole* holeptr;
	Core* coreptr;
	Strat* stratptr;
	for(int i=0; i < numHoles; i++)
	{
		holeptr = dataptr->getHole(i);
		if (holeptr == NULL) continue;
		numCores =  holeptr->getNumOfCores();
		for(int j=0; j < numCores; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			numStrats = coreptr->getNumOfStrat();
			for(int k=0; k < numStrats; k++)
			{
				stratptr = coreptr->getStrat(k);
				if(stratptr == NULL) continue;
				if(stratptr->getOrder() == order)
				{
					return stratptr;
				}
			}
		}
	}
	return NULL;
}

int WriteStratTable( FILE *fptr, Data* dataptr )
{	
	if(dataptr == NULL) return 0;


	const char* site = dataptr->getSite();
	const char* leg = dataptr->getLeg();

	Hole* holeptr = NULL;
	Core* coreptr = NULL;

	fprintf (fptr, "# No, Datum Name, Label, Type, Age top, Age Bottom, Leg, Site, Hole, Core No, Section Type, Section No, Interval, Mbsf, Leg, Site, Hole, Core No, Section Type, Section No, Interval, Mbsf\n");
	fprintf (fptr, "# Generated By Correlator\n");

	// how many real-tie
    int numHoles = dataptr->getNumOfHoles();
    int numCores, numStrats;
    int count=0;
    for(int i=0; i < numHoles; i++)
    {
    	holeptr = dataptr->getHole(i);
    	if (holeptr == NULL) continue;
    	numCores =  holeptr->getNumOfCores();
    	for(int j=0; j < numCores; j++)
    	{
    		coreptr = holeptr->getCore(j);
    		if (coreptr == NULL) continue;
    		numStrats = coreptr->getNumOfStrat();
    		count += numStrats;
    	}
    }
	if (count == 0) return 0;

	Strat* stratptr = NULL;
	
  	for(int i=0; i < count; i++)
	{
		stratptr = findStrat(dataptr, i);
		if(stratptr)
		{
			fprintf (fptr, "%s \t%s \t%d \t%f \t%f ", stratptr->getDatumName(), stratptr->getCode(), stratptr->getDataType(), stratptr->getTopAge(), stratptr->getBotAge());  
			fprintf (fptr, "\t%s \t%s \t%c \t%d \t%c \t%s \t%f \t%f ", leg, site, stratptr->getHoleName(),  stratptr->getTopCoreNumber(), stratptr->getTopType(), stratptr->getTopSection(), stratptr->getTopInterval(), stratptr->getTopMbsf());  
			fprintf (fptr, "\t%s \t%s \t%c \t%d \t%c \t%s \t%f \t%f\n", leg, site, stratptr->getHoleName(),  stratptr->getBotCoreNumber(), stratptr->getBotType(), stratptr->getBotSection(), stratptr->getBotInterval(), stratptr->getBotMbsf());  
		} else 
			break;
	}

	return 1;
}

int WriteLog( FILE *fptr, Data* dataptr, char* label )
{
	if (dataptr == NULL) return 0;
	
	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	int coresize, valuesize;

	holeptr = dataptr->getHole(0);
	if(holeptr == NULL) return 0;
	fprintf (fptr, " HOLE: %s%s\n", dataptr->getSite(), holeptr->getName());	
	fprintf (fptr, " LEG: %s\n", dataptr->getLeg());		
	fprintf (fptr, " TOP: %f\n", holeptr->getMinDepth());
	fprintf (fptr, " BOTTOM: %f\n\n", holeptr->getMaxDepth());

	fprintf (fptr, " DEPTH 	DATA\n");

	coresize = holeptr->getNumOfCores();
	for(int i=0; i < coresize; i++)
	{
		coreptr = holeptr->getCore(i);
		if(coreptr == NULL) continue;
		valuesize = coreptr->getNumOfValues();
		for(int j=0; j < valuesize; j++)
		{
			valueptr = coreptr->getValue(j);
			if(valueptr == NULL) continue;
			fprintf (fptr, "%f \t%f\n", valueptr->getMbsf(), valueptr->getData());
			
		}
	}

	return 1;
}

int ReadSplice( FILE *fptr, Data* dataptr )
{
	if(dataptr == NULL) return 0;

	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);

	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);

	dataptr->setType(SPLICE);
	
	Hole* newHole = NULL;
	char* hole_name = NULL;
	int hole_index = dataptr->getNumOfHoles() -1;

	Core* newCore = NULL;
	int core_index;
	
	Value* newValue = NULL;
	int value_index;
	char* temp_hole_name = NULL;
					
	while(fgets(line, MAX_LINE, fptr)!=NULL)
	{

		// set leg, subleg(?), site
		getToken(line, token);	
		if(token[0] == '#')
		{
			token_num = 0;
			continue;
		}
				
		dataptr->setLeg(token);
		getToken(line, token);					
		dataptr->setSite(token);	
		getToken(line, token);					
		toupper(&token[0]);	
		temp_hole_name = &token[0];	

		// check if new hole
		if(hole_name ==NULL || (strcmp(hole_name, temp_hole_name)  != 0))
		{
			hole_name = &token[0];

			newHole = dataptr->getHole(hole_name, SPLICE, SPLICE);
			if(newHole == NULL) 
			{
				hole_index++;			
				// create new Hole  
				newHole = dataptr->createHole(hole_index, hole_name, SPLICE);
				if(newHole == NULL) return 0;
				newHole->setDataFormat(SPLICED_RECORD);				
				newHole->setType(SPLICE);
				//newHole->setName(hole_name);
				core_index = -1;
			}   
		}			
		
		// core index
		getToken(line, token);			
		// check if new core		
		if(core_index != atoi(token)) 
		{
			core_index = atoi(token);
			newCore = newHole->getCore(core_index);
			if(newCore == NULL)
			{
				newCore = newHole->createCore(core_index);
				newCore->setNumber(core_index);	
				newCore->setType(OTHERTYPE);	
				value_index = -1;
			} else 
			{
				value_index = newCore->getNumOfValues() -1;
			}
		}
		
		value_index++;		
		newValue = newCore->createValue(value_index);
		
		getToken(line, token);				
		toupper(&token[0]);
		
		newValue->setType(token[0]);
		
		// todo : make section... ????
		// section info
		getToken(line, token);				
		toupper(&token[0]);	
		newValue->setSection(token);

		data_range range;
		getToken(line, token);				
		range.top = atof(token);		
		getToken(line, token);				
		range.bottom = atof(token);	
		newValue->setRange(range);
		
		getToken(line, token);						
		//newValue->setDepth(atof(token));
		//newValue->setMbsf(atof(token));
		
		getToken(line, token);						
		newValue->setRawData(atof(token));
		getToken(line, token);						
		newValue->setData(atof(token));

		getToken(line, token);	
		newCore->setDepthOffset(atof(token), false, true);

		getToken(line, token);		
		newValue->setDepth(atof(token));
		newValue->setMbsf(atof(token));						

		getToken(line, token);	
		newCore->setAnnotation(token);
		
	}
	   
	return 1;
}

int WriteSplice( FILE *fptr,  Hole* dataptr, const char* leg, const char* site )
{
	if(dataptr == NULL) return 0;

	// Site	Hole	Core	Type	Sect	Int1	Int2	mbsf	RAwValue	SmValue
	// Offset	mcd
	// EXAMPLE:
	// 926     B       1       H       1       7.50    7.50    0.08    10.00   10.00
	// 0.00    0.08
	
	//int leg = dataptr->getLeg();
	//int site = dataptr->getSite();
	fprintf (fptr, "# Leg, Site, Hole, Core No, Section Type, Section No, top, bottom, total, raw data, smooth data, offset, depth, annotation\n");
	fprintf (fptr, "# Generated By Correlator\n");
	
	
	Hole* holeptr = dataptr;
	Core* coreptr = NULL;
	Value* valueptr = NULL;

	// how many real-tie
	int numCores, numValues;

	numCores = holeptr->getNumOfCores();
	for(int i=0; i < numCores; i++)
	{
		coreptr = holeptr->getCore(i);
		if(coreptr == NULL) continue;
		numValues = coreptr->getNumOfValues();
		for(int j=0; j < numValues; j++)
		{
			valueptr = coreptr->getValue(j);
			if(valueptr == NULL) continue;
			//fprintf (fptr, "%s %s %s %d %c %s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());

			fprintf (fptr, "%s %s spliced_record %d %c %s", leg, site, coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
			fprintf (fptr, " \t%f %f \t%f ", valueptr->getTop(), valueptr->getBottom(), valueptr->getDepth());
			fprintf (fptr, "\t%f %f \t%f \t%f \t%s\n", valueptr->getRawData(),  valueptr->getData(), coreptr->getDepthOffset(), valueptr->getMcd(), coreptr->getAnnotation() );
		}
	} 

	return 1;
}

int WriteAgeSplice( FILE *fptr, FILE *temp_fptr, Hole* dataptr, const char* leg, const char* site )
{
	if(dataptr == NULL) return 0;

	// Site	Hole	Core	Type	Sect	Int1	Int2	mbsf	RAwValue	SmValue
	// Offset	mcd
	// EXAMPLE:
	// 926     B       1       H       1       7.50    7.50    0.08    10.00   10.00
	// 0.00    0.08
	
	//int leg = dataptr->getLeg();
	//int site = dataptr->getSite();
	fprintf (fptr, "# Leg, Site, Hole, Core No, Section Type, Section No, top, bottom, total, raw data, smooth data, offset, depth, Age, annotation\n");
	fprintf (fptr, "# Generated By Correlator\n");
	
	
	Hole* holeptr = dataptr;
	Core* coreptr = NULL;
	Value* valueptr = NULL;

	// how many real-tie
	int numCores, numValues;

	numCores = holeptr->getNumOfCores();
	
	if(temp_fptr == NULL)
	{
		for(int i=0; i < numCores; i++)
		{
			coreptr = holeptr->getCore(i);
			if(coreptr == NULL) continue;
			numValues = coreptr->getNumOfValues();
			for(int j=0; j < numValues; j++)
			{
				valueptr = coreptr->getValue(j);
				if(valueptr == NULL) continue;
							fprintf (fptr, "%s %s %s %d %c %s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
							fprintf (fptr, " \t%f %f \t%f ", valueptr->getTop(), valueptr->getBottom(), valueptr->getDepth());
							fprintf (fptr, "\t%f %f \t%f \t%f \t0.00 \t%s\n", valueptr->getRawData(),  valueptr->getData(), coreptr->getDepthOffset(), valueptr->getMcd(), coreptr->getParent()->getAnnotation() );
			}
		} 
	} else 
	{
		double age= 0.0f;

		char	line[MAX_LINE];
		memset(line, 0, MAX_LINE);
		char token[TOKEN_LEN];
		memset(token, 0, TOKEN_LEN);


		for(int i=0; i < numCores; i++)
		{
			coreptr = holeptr->getCore(i);
			if(coreptr == NULL) continue;
			numValues = coreptr->getNumOfValues();
			for(int j=0; j < numValues; j++)
			{
				if(fgets(line, MAX_LINE, temp_fptr)!=NULL)
				{
					getToken(line, token);
					age = atof(token);
					token_num = 0;
				}
				valueptr = coreptr->getValue(j);
				if(valueptr == NULL) continue;
							fprintf (fptr, "%d %d %s %d %c %s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
							fprintf (fptr, " \t%f %f \t%f ", valueptr->getTop(), valueptr->getBottom(), valueptr->getDepth());
							fprintf (fptr, "\t%f %f \t%f \t%f \t%f \t%s\n", valueptr->getRawData(),  valueptr->getData(), coreptr->getDepthOffset(), valueptr->getMcd(), age, coreptr->getParent()->getAnnotation() );
			}
		} 	
	}
	
	return 1;
}

int ReadXMLFile(const char* fileName, Data* dataptr)
{
	/*try
    {
         XMLPlatformUtils::Initialize();
    }
    catch (const XMLException& err)
    {
		//MessageBox(NULL,err.what(),"ERROR INITIALIZING XML PARSER",MB_OK|MB_ICONEXCLAMATION);
        return 0;
    }

	SAXParser parser;
	CXMLLoader *pHandler = new CXMLLoader(dataptr);
    try
    {
        parser.setDocumentHandler(pHandler);
        parser.setErrorHandler(pHandler);
        parser.parse(fileName);
    }
    catch (const XMLException& err)
    {
		//MessageBox(NULL,err.getMessage(),"ERROR PARSING XML FILE",MB_OK|MB_ICONEXCLAMATION);
    }
	
	delete pHandler;
	*/
	cout << "[DEBUG-ERROR] Read xml was called -It is deleted" << endl;
	return 1;

}

int WriteCoreData( char* filename, Data* dataptr )
{
	if (dataptr == NULL) return 0;
	if (filename == NULL) return 0;
	string fullpath(filename);	
	string extfullpath = "";
	FILE *fptr= NULL;
#ifdef DEBUG	
	cout << "[DEBUG] WriteCoreData " << filename << endl;
#endif	
	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	char* holename = NULL;
	int coresize =0;
	int valuesize =0;
	double sum_test;
	
	const char* leg = dataptr->getLeg();
   	const char* site = dataptr->getSite();
	//char subname[10];
	//memset(subname, 0, 10);
	//sprintf(subname, "-%d-%d-", leg, site);
	int holesize = dataptr->getNumOfHoles();
	string str_type = "";
	char num[2];
	
	for(int i=0; i < holesize; i++)
	{
		holeptr = dataptr->getHole(i);
		if(holeptr == NULL) continue;

		holename = (char*) holeptr->getName();
		
		extfullpath = filename;
		//extfullpath += subname;
		memset(num, 0, 2);
		sprintf(num,"%d",i);
		extfullpath += num;
		//extfullpath += ".dat";
		fptr = fopen(extfullpath.c_str(),"w+");
		if(fptr == NULL) continue;
		fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data RunNo RawDepth Offset\n");

		str_type = holeptr->getTypeStr();
		fprintf (fptr, "# Data Type %s\n", str_type.c_str());
		fprintf (fptr, "# Generated By Correlator\n");		

		coresize = holeptr->getNumOfCores();
		for(int k=0; k < coresize; k++)
		{
			coreptr = holeptr->getCore(k);
			if(coreptr == NULL) continue;
			valuesize = coreptr->getNumOfValues();
			for(int j=0; j < valuesize; j++)
			{
				valueptr = coreptr->getValue(j);
				if(valueptr == NULL) continue;
				if(valueptr->getQuality() ==GOOD)
				{
					if(valueptr->getValueType() == INTERPOLATED_VALUE) continue;
					
#ifdef NEWOUTPUT
					string dataLine;
					const string format("sssicsffffcff");
					makeDelimString(format, dataLine, leg, site, holeptr->getName(), coreptr->getNumber(),
					                valueptr->getType(), valueptr->getSection(), valueptr->getTop(), valueptr->getBottom(),
					                valueptr->getELD(), valueptr->getRawData(), '-', valueptr->getMbsf(), coreptr->getDepthOffset());
					dataLine += '\n';
					fprintf(fptr, "%s", dataLine.c_str());
#else
					fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
					fprintf (fptr, " \t%f \t%f \t%f \t%f \t- \t%f \t%f\n", valueptr->getTop(), valueptr->getBottom(), valueptr->getELD(), valueptr->getRawData(), valueptr->getMbsf(), coreptr->getDepthOffset());
#endif // NEWOUTPUT

					sum_test = valueptr->getMbsf() + coreptr->getDepthOffset() ;
					/*if (sum_test != valueptr->getMcd())
						cout << "ERROR >>>>> AT " << holeptr->getName() << coreptr->getNumber() << " " << valueptr->getTop() << " " << valueptr->getBottom() << " " << valueptr->getELD() << endl;
					if (valueptr->getELD() != valueptr->getMcd())
						cout << "ERROR ELD? >>>>> AT " << holeptr->getName() << coreptr->getNumber() << " " << valueptr->getTop() << " " << valueptr->getBottom() << " " << valueptr->getELD() << endl;
					*/
				}
			}
		}
		
		fclose(fptr);
	}	
	return holesize;
}

int WriteCoreHole( char* filename, Hole* holeptr )
{
	if (holeptr == NULL) return 0;
	if (filename == NULL) return 0;	
	FILE *fptr= NULL;
#ifdef DEBUG	
	cout << "[DEBUG] WriteCoreHole " << filename << endl;
#endif	
	const char* leg = holeptr->getLeg();
   	const char* site = holeptr->getSite();
	string str_type = "";
	double sum_test;
	
	char* holename = (char*) holeptr->getName();
	fptr = fopen(filename,"w+");
	if(fptr == NULL) return 0;
	
	if (holeptr->getType() == SPLICED_RECORD)
	{
		fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data RunNo Annotation RawDepth Offset\n");
	} else {
		fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data RunNo RawDepth Offset\n");
		str_type = holeptr->getTypeStr();
	}

#ifdef DEBUG	
	cout << "[DEBUG] Export Core : Data type == " << holeptr->getType() << endl;
#endif	
	fprintf (fptr, "# Data Type %s\n", str_type.c_str());
	fprintf (fptr, "# Generated By Correlator\n");		

	int coresize = holeptr->getNumOfCores();
	
#ifdef DEBUG	
	cout << "[DEBUG] Export Core : core size = " << coresize << endl;
#endif

	int valuesize =0;	
	Core* coreptr = NULL;
	Value* valueptr = NULL;

	vector<char> name_list;
	vector<char>::iterator name_iter;
	const char* annot;
	char name;
	bool found;
	for(int j=0; j < coresize; j++)
	{
		coreptr = holeptr->getCore(j);
		if(coreptr == NULL) continue;
		annot = coreptr->getParent()->getAnnotation();
		if(annot != NULL)
		{
			found = false;
			name = annot[0];
			for(name_iter = name_list.begin(); name_iter != name_list.end(); name_iter++)
			{
				if(*name_iter == name)
				{
					found = true;
					break;
				}
			}
			if (found == false)
			{
				name_list.push_back(name);
			}
		}
	}
	
	string name_str = "";
	for(name_iter = name_list.begin(); name_iter != name_list.end(); name_iter++)
	{
		name_str += *name_iter;
	}
	if ((holeptr->getType() != SPLICED_RECORD) && (holeptr->getType() != ELD_RECORD))
	{
		for(int i=0; i < coresize; i++)
		{
			coreptr = holeptr->getCore(i);
			if(coreptr == NULL) continue;
			valuesize = coreptr->getNumOfValues();
			for(int j=0; j < valuesize; j++)
			{
				valueptr = coreptr->getValue(j);
				if(valueptr == NULL) continue;
				if(valueptr->getQuality() ==GOOD)
				{
					if(valueptr->getValueType() == INTERPOLATED_VALUE) continue;

#ifdef NEWOUTPUT
					// brgbrg
					string dataLine;
					const string format("sssicsffffcsff");
					makeDelimString(format, dataLine, leg, site, name_str.c_str(), coreptr->getNumber(),
					                valueptr->getType(), valueptr->getSection(), valueptr->getTop(), valueptr->getBottom(),
					                valueptr->getELD(), valueptr->getRawData(), '-', coreptr->getParent()->getAnnotation(),
					                valueptr->getMbsf(), coreptr->getDepthOffset());
					dataLine += '\n';
					fprintf(fptr, "%s", dataLine.c_str());
#else
					//fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
					fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, name_str.c_str(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());

					fprintf (fptr, " \t%f \t%f \t%f \t%f \t- \t%s \t%f \t%f\n", valueptr->getTop(), valueptr->getBottom(), valueptr->getELD(), valueptr->getRawData(), coreptr->getParent()->getAnnotation(), valueptr->getMbsf(), coreptr->getDepthOffset());
#endif // NEWOUTPUT

					sum_test = valueptr->getMbsf() + coreptr->getDepthOffset() ;
					/*if (sum_test != valueptr->getMcd())
						cout << "ERROR >>>>> AT " << holeptr->getName() << coreptr->getNumber() << " " << valueptr->getTop() << " " << valueptr->getBottom() << " " << valueptr->getELD() << endl;
					if (valueptr->getELD() != valueptr->getMcd())
						cout << "ERROR ELD? >>>>> AT " << holeptr->getName() << coreptr->getNumber() << " " << valueptr->getTop() << " " << valueptr->getBottom() << " " << valueptr->getELD() << endl;
					*/
				}
			}
		}
	}
	else 
	{
		int j = 0;
		for (int i = 0; i < coresize; i++)
		{
			coreptr = holeptr->getCore(i);
			if (coreptr == NULL) continue;
			valuesize = coreptr->getNumOfValues();
			for (j = 0; j < valuesize; j++)
			{
				valueptr = coreptr->getValue(j);
				if (valueptr == NULL) continue;
				if (valueptr->getValueType() == INTERPOLATED_VALUE) continue;
				if (valueptr->getQuality() == GOOD)
				{
#ifdef NEWOUTPUT
					string dataLine;
					const string format("sssicsffffcsff");
					makeDelimString(format, dataLine, leg, site, "spliced_record", coreptr->getNumber(),
					                valueptr->getType(), valueptr->getSection(), valueptr->getTop(), valueptr->getBottom(),
					                valueptr->getELD(), valueptr->getRawData(), '-', coreptr->getAnnotation(),
					                valueptr->getMbsf(), coreptr->getDepthOffset());
					dataLine += '\n';
					fprintf(fptr, "%s", dataLine.c_str());
#else

					//fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
					fprintf (fptr, "%s \t%s \tspliced_record \t%d \t%c \t%s", leg, site, coreptr->getNumber(), valueptr->getType(), valueptr->getSection());

					fprintf (fptr, " \t%f \t%f \t%f \t%f \t-", valueptr->getTop(), valueptr->getBottom(), valueptr->getELD(), valueptr->getRawData());

					// 9/26/2013 brg: Omit interpolated values entirely for now
					//if (valueptr->getValueType() == INTERPOLATED_VALUE)
					//{
					//	fprintf (fptr, " \ti%s \t%f \t%f\n", coreptr->getAnnotation(), valueptr->getMbsf(), coreptr->getDepthOffset());
					//}
					//else 
					//{
						fprintf (fptr, " \t%s \t%f \t%f\n", coreptr->getAnnotation(), valueptr->getMbsf(), coreptr->getDepthOffset());					
					//}
#endif // NEWOUTPUT
				}
			}
		}	
	}
		
	fclose(fptr);

	return 1;
}

int WriteAgeCoreData( char* agefilename, char* filename, Data* dataptr, int appliedflag )
{
	if (dataptr == NULL) return 0;
	if (filename == NULL) return 0;
	if (agefilename == NULL) return 0;

	string fullpath(filename);	
	string extfullpath = "";
	FILE *fptr= NULL;
	
	//cout << "WriteCoreData " << filename << endl;
	
	Hole* holeptr = NULL;
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	char* holename = NULL;
	int coresize =0;
	int valuesize =0;
	
	const char* leg = dataptr->getLeg();
   	const char* site = dataptr->getSite();
	
	// HEEEE
	FILE *agefptr= NULL;
	agefptr = fopen(agefilename,"r+");
	if(agefptr == NULL) return 0;
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	double mbsf, mcd, eld, age, sedrate;
	vector<age_model_st> age_model_list;
	while(fgets(line, MAX_LINE, agefptr)!=NULL)
	{
		// Leg, Site, Mbsf, Mcd, Eld, Age, Sediment Rate, Age Datum, Comment, Type
		getToken(line, token);
		if(token[0] == '#') 
		{
			token_num = 0;
			continue;
		}
		
		age_model_st age_model;
		getToken(line, token);	

		getToken(line, token);	
		age_model.mbsf = atof(token);
		
		getToken(line, token);	
		age_model.mcd = atof(token);
		getToken(line, token);	
		age_model.eld = atof(token);
		
		getToken(line, token);	
		age_model.age = atof(token);
		getToken(line, token);	
		age_model.sedrate = atof(token);
		age_model_list.push_back(age_model);
		token_num = 0;
	}
	fclose(agefptr);
	
	age_model_st age_point;
	vector<age_model_st>::iterator age_iter;
		
	//char subname[10];
	//memset(subname, 0, 10);
	//sprintf(subname, "-%d-%d-", leg, site);
	int holesize = dataptr->getNumOfHoles();
	string str_type = "";
	char num[2];
	double age_rate, prev_mbsf, prev_age;
	int count =0;
	double age_offset = 0;
	int where = 2;
	
	for(int i=0; i < holesize; i++)
	{
		holeptr = dataptr->getHole(i);
		if(holeptr == NULL) continue;

		holename = (char*) holeptr->getName();
		
		extfullpath = filename;
		//extfullpath += subname;
		memset(num, 0, 2);
		sprintf(num,"%d",i);
		extfullpath += num;
		//extfullpath += ".dat";
		fptr = fopen(extfullpath.c_str(),"w+");
		if(fptr == NULL) continue;
		// appliedflag = 0, appliedflag = 1 (affine), appliedflag = 2 (eld)	
		if (appliedflag == 0)
			fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(CSF) Age(Ma)\n");
		else if (appliedflag == 1)
			fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(CCSF) Age(Ma)\n");
		else 
			fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(eld) Age(Ma)\n");

		str_type = holeptr->getTypeStr();

		fprintf (fptr, "# Data Type %s\n", str_type.c_str());
		fprintf (fptr, "# Generated By Correlator\n");		

		coresize = holeptr->getNumOfCores();
		for(int j=0; j < coresize; j++)
		{
			coreptr = holeptr->getCore(j);
			if(coreptr == NULL) continue;
			valuesize = coreptr->getNumOfValues();
			for(int j=0; j < valuesize; j++)
			{
				valueptr = coreptr->getValue(j);
				if(valueptr == NULL) continue;
				if(valueptr->getQuality() ==GOOD)
				{
					mbsf = valueptr->getELD();
					age_rate = 1.0f;
					count =0;
					where = 2;
					for(age_iter = age_model_list.begin(); age_iter != age_model_list.end(); age_iter++)
					{
						age_point = *age_iter;
						if(count == 0)
						{
							prev_mbsf = age_point.eld;
							prev_age = age_point.age;
							sedrate = age_point.sedrate;
							count ++;
							if(prev_mbsf >= mbsf)
							{
								where = 0;
								break;
							}
							continue;
						}
							
						if((prev_mbsf <= mbsf) && (age_point.eld > mbsf))
						{
							age_rate = (age_point.age - prev_age) / ((age_point.eld - prev_mbsf) * 1.0f);
							age = prev_age + (mbsf - prev_mbsf) * age_rate; 
							sedrate = age_point.sedrate;
							prev_mbsf = age_point.eld;
							prev_age = age_point.age;	
							where = 1;
							break;
						}
						prev_mbsf = age_point.eld;
						prev_age = age_point.age;	
						sedrate = age_point.sedrate;					
					}

					if (where != 1)
					{
						age =  (mbsf - prev_mbsf) + prev_age;
					} 	
#ifdef NEWOUTPUT
					// brgbrg
					string dataLine;
					const string format("sssicsfffffff");
					makeDelimString(format, dataLine, leg, site, holeptr->getName(), coreptr->getNumber(), // sssi
					                valueptr->getType(), valueptr->getSection(), valueptr->getTop(), valueptr->getBottom(), // csff
					                valueptr->getMbsf(), valueptr->getRawData(), sedrate, valueptr->getELD(), age); // fffff
					dataLine += '\n';
					fprintf(fptr, "%s", dataLine.c_str());
#else
					//Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(m) Age(Ma)
					fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
					fprintf (fptr, " \t%f \t%f \t%f \t%f", valueptr->getTop(), valueptr->getBottom(), valueptr->getMbsf(), valueptr->getRawData());
					fprintf (fptr, " \t%f \t%f \t%f\n", sedrate, valueptr->getELD(), age);
#endif // NEWOUTPUT
				}
			}
		}
		
		fclose(fptr);
	}	
	return holesize;
}

int WriteAgeCoreHole( char* agefilename, char* filename, Hole* holeptr, int appliedflag )
{
	if (holeptr == NULL) return 0;
	if (filename == NULL) return 0;	
	if (agefilename == NULL) return 0;

	FILE *fptr= NULL;
	//cout << "WriteCoreData " << filename << endl;
	
	const char* leg = holeptr->getLeg();
   	const char* site = holeptr->getSite();

	FILE *agefptr= NULL;
	agefptr = fopen(agefilename,"r+");
	if(agefptr == NULL) return 0;
	char	line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);
	
	double mbsf, mcd, eld, age, sedrate;
	vector<age_model_st> age_model_list;
	while(fgets(line, MAX_LINE, agefptr)!=NULL)
	{
		// Leg, Site, Mbsf, Mcd, Eld, Age, Sediment Rate, Age Datum, Comment, Type
		getToken(line, token);
		if(token[0] == '#') 
		{
			token_num = 0;
			continue;
		}
		
		age_model_st age_model;
		getToken(line, token);	

		getToken(line, token);	
		age_model.mbsf = atof(token);
		
		getToken(line, token);	
		age_model.mcd = atof(token);
		getToken(line, token);	
		age_model.eld = atof(token);
		
		getToken(line, token);	
		age_model.age = atof(token);
		getToken(line, token);	
		age_model.sedrate = atof(token);
		age_model_list.push_back(age_model);
		token_num = 0;
	}
	fclose(agefptr);
	age_model_st age_point;
	vector<age_model_st>::iterator age_iter;

	string str_type = "";
	char* holename = (char*) holeptr->getName();
	fptr = fopen(filename,"w+");
	if(fptr == NULL) return 0;
	// appliedflag = 0, appliedflag = 1 (splice), appliedflag = 2 (eld)
	if (appliedflag == 0)
		fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(CSF) Age(Ma)\n");
	else if (appliedflag == 1)
		fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(CCSF) Age(Ma)\n");
	else 
		fprintf (fptr, "# Leg Site Hole Core CoreType Section TopOffset BottomOffset Depth Data SedRate Depth(eld) Age(Ma)\n");

	str_type = holeptr->getTypeStr();
	
#ifdef DEBUG	
	cout << "[DEBUG] Export Core : Data type == " << holeptr->getType() << endl;
#endif	
	fprintf (fptr, "# Data Type %s\n", str_type.c_str());
	fprintf (fptr, "# Generated By Correlator\n");		

	int coresize = holeptr->getNumOfCores();
#ifdef DEBUG	
	cout << "[DEBUG] Export Core : core size = " << coresize << endl;
#endif	
	int valuesize =0;	
	Core* coreptr = NULL;
	Value* valueptr = NULL;
	
	vector<char> name_list;
	vector<char>::iterator name_iter;
	const char* annot;
	char name;
	bool found;
	for(int j=0; j < coresize; j++)
	{
		coreptr = holeptr->getCore(j);
		if(coreptr == NULL) continue;
		annot = coreptr->getParent()->getAnnotation();
		if(annot != NULL)
		{
			found = false;
			name = annot[0];
			for(name_iter = name_list.begin(); name_iter != name_list.end(); name_iter++)
			{
					if(*name_iter == name)
					{
						found = true;
						break;
					}
			}
			if (found == false)
			{
				name_list.push_back(name);
			}
		}
	}
	
	string name_str = "";
	for(name_iter = name_list.begin(); name_iter != name_list.end(); name_iter++)
	{
		name_str += *name_iter;
	}

	double age_rate, prev_mbsf, prev_age;
	int count =0;
	double age_offset = 0;
	int where = 2;	

	for(int j=0; j < coresize; j++)
	{
		coreptr = holeptr->getCore(j);
		if(coreptr == NULL) continue;
		valuesize = coreptr->getNumOfValues();
		for(int j=0; j < valuesize; j++)
		{
			valueptr = coreptr->getValue(j);
			if(valueptr == NULL) continue;
			if(valueptr->getQuality() ==GOOD)
			{
				mbsf = valueptr->getELD();
				age_rate = 1.0f;
				count =0;
				where = 2;
				for(age_iter = age_model_list.begin(); age_iter != age_model_list.end(); age_iter++)
				{
					age_point = *age_iter;
					if(count == 0)
					{
						prev_mbsf = age_point.eld;
						prev_age = age_point.age;
						sedrate = age_point.sedrate;
						count ++;
						if(prev_mbsf >= mbsf)
						{
							where = 0;
							break;
						}
						continue;
					}
						
					if((prev_mbsf <= mbsf) && (age_point.eld > mbsf))
					{
						age_rate = (age_point.age - prev_age) / ((age_point.eld - prev_mbsf) * 1.0f);
						age = prev_age + (mbsf - prev_mbsf) * age_rate; 
						sedrate = age_point.sedrate;
						prev_mbsf = age_point.eld;
						prev_age = age_point.age;	
						where = 1;
						break;
					}
					prev_mbsf = age_point.eld;
					prev_age = age_point.age;	
					sedrate = age_point.sedrate;					
				}

				if (where != 1)
				{
					age =  (mbsf - prev_mbsf) + prev_age;
				}			

#ifdef NEWOUTPUT
				// brgbrg
				string dataLine;
				const string format("sssicsfffffffs");
				makeDelimString(format, dataLine, leg, site, name_str.c_str(), coreptr->getNumber(), // sssi
				                valueptr->getType(), valueptr->getSection(), valueptr->getTop(), valueptr->getBottom(), // csff
				                valueptr->getMbsf(), valueptr->getRawData(), sedrate, valueptr->getELD(), age, // fffff
				                coreptr->getParent()->getAnnotation()); // s
				dataLine += '\n';
				fprintf(fptr, "%s", dataLine.c_str());
#else
				//fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, holeptr->getName(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
				fprintf (fptr, "%s \t%s \t%s \t%d \t%c \t%s", leg, site, name_str.c_str(), coreptr->getNumber(), valueptr->getType(), valueptr->getSection());
				fprintf (fptr, " \t%f \t%f \t%f \t%f", valueptr->getTop(), valueptr->getBottom(), valueptr->getMbsf(), valueptr->getRawData());
				fprintf (fptr, " \t%f \t%f \t%f \t%s\n", sedrate, valueptr->getELD(), age, coreptr->getParent()->getAnnotation());
#endif // NEWOUTPUT
			}
		}
	}
	
	fclose(fptr);

	return 1;
}


int readline(char* line, FILE* rfptr, int uft_16)
{
	int i =0;
	if(uft_16 == 0) 
	{
		char temp = fgetc(rfptr);
		int k =0;
		while(temp == 10)
		{
			temp = fgetc(rfptr);
			k++;
		} 
		line[i] = temp;
		while(temp != 13 && temp != EOF && temp != 10)
		{
			i++;
			if(i >= MAX_LINE) return -1;
			
			temp = fgetc(rfptr);
			if(temp == '\t')
				line[i] = ' ';
			else 
				line[i] = temp;
			if (int(line[i]) == 13)
			{
				break;
			}
		} 
		if(line[i] == EOF) return -1;
	} else 
	{
		fgetc(rfptr);fgetc(rfptr);
		char temp = fgetc(rfptr);
		while(temp != 13 && temp != EOF)
		{
			if(temp > 0) 
			{
				line[i] = temp;
				i++;
				if(i >= MAX_LINE) return -1;
			}
			temp = fgetc(rfptr);
		} 
		if(temp == EOF) return -1;	
	}
	
	return 1;
}

int	WriteLog( char* read_filename, char* write_filename, int depth_idx, int data_idx )
{
	char line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);	
	
	FILE *rfptr= NULL;
	rfptr= fopen(read_filename,"r+");
	if(rfptr == NULL) 
	{
#ifdef DEBUG	
		cout << " cound not open as read" << endl;
#endif
		return -1;
	}

	FILE *wfptr= NULL;
	
	wfptr= fopen(write_filename,"a+");
	if(wfptr == NULL) 
	{
#ifdef DEBUG	
		cout << " cound not open as write" << endl;
#endif
		fclose(rfptr);
		return -1;
	}

	int uft_16 = 0;
	fgets(line, MAX_LINE, rfptr);
	if((int(line[0]) < 0) || (int(line[1]) < 0))
	{
		uft_16 = 1;
#ifdef DEBUG		
		cout << "uft_16 mode " << endl;
#endif
	}
	
	fseek(rfptr, 0L, SEEK_SET);
	memset(line, 0, MAX_LINE);
	double depth, data;
	int index,max;
			
	while(readline(line, rfptr, uft_16) >= 0)
	{
		if ((line[0] >= 'A' && line[0] <= 'Z') || (line[0] >= 'a' && line[0] <= 'z') || (line[0] == '#'))
		{
			token_num = 0;
			memset(line, 0, MAX_LINE);
			continue;
		}
		
		depth =-999;
		data =-999;
		index = 0;
		//std::cout << line;
		max =getToken(line, token) +1;
		//std::cout << " " <<  max << std::endl;
		
		for(int i=0; i < max;  i++)
		{
			if(depth_idx == i)
				depth = atof(token);
			else if (data_idx == i)
				data = atof(token);				
			getToken(line, token);
		}
		if((depth != -999) && (data !=-999))
		{
#ifdef NEWOUTPUT
			// brgbrg
			string dataLine;
			const string format("ff");
			makeDelimString(format, dataLine, depth, data);
			dataLine += '\n';
			fprintf(wfptr, "%s", dataLine.c_str());
#else
			fprintf (wfptr, "%.5f \t%.5f \t\n", depth, data);
#endif // NEWOUTPUT
		}
	}
	
	fclose(rfptr);
	fclose(wfptr);
	
	//string temp = "mv temp.dat ";
	//temp += filename;
	//system(temp.c_str());
	
	return 1;	
}


int ChangeFormat(const char* infilename, const char* outfilename)
{
	char line[MAX_LINE];
	memset(line, 0, MAX_LINE);
	char token[TOKEN_LEN];
	memset(token, 0, TOKEN_LEN);	
	
	FILE *rfptr= NULL;
	rfptr= fopen(infilename,"r+");
	if(rfptr == NULL) 
	{
#ifdef DEBUG	
		cout << " cound not open as read" << endl;
#endif
		return -1;
	}

	FILE *wfptr= NULL;
	string outfile = outfilename;
	outfile += "tmp.core";
	
	wfptr= fopen(outfile.c_str(),"w+");
	if(wfptr == NULL) 
	{
#ifdef DEBUG	
		cout << " cound not open as write" << endl;
#endif
		fclose(rfptr);
		return -1;
	}	
	
	int total_count = 0;
	memset(line, 0, MAX_LINE);

	int uft_16 = 0;
	fgets(line, MAX_LINE, rfptr);
	if((int(line[0]) < 0) || (int(line[1]) < 0))
	{
		uft_16 = 1;
#ifdef DEBUG		
		cout << "uft_16 mode " << endl;
#endif
	}
	
	fseek(rfptr, 0L, SEEK_SET);
	memset(line, 0, MAX_LINE);
	if(readline(line, rfptr, uft_16) < 0) return -1;
	
	while ((line[0] >= 'A' && line[0] <= 'Z') || (line[0] >= 'a' && line[0] <= 'z') || (line[0] == '#') )
	{
		//fgets(line, MAX_LINE, rfptr);
		memset(line, 0, MAX_LINE);
		if(readline(line, rfptr, uft_16) < 0) return -1;
	}
	//
	do
	{
		getToken(line, token);	
		total_count ++;
	} while(token_num != 0);
	
	fseek(rfptr, 0L, SEEK_SET);
	//while(fgets(line, MAX_LINE, rfptr)!=NULL)
	memset(line, 0, MAX_LINE);
	int ret;
	int difference = 0;
	int index = 0;
	int loop_total = 0;
	while(readline(line, rfptr, uft_16) >= 0)
	{

		if ((line[0] >= 'A' && line[0] <= 'Z') || (line[0] >= 'a' && line[0] <= 'z') || (line[0] == '#'))
		{
			token_num = 0;
			memset(line, 0, MAX_LINE);
			continue;
		}

		//fprintf (wfptr, " ");	
		index = getToken(line, token);
		if(token[0] == '-')
		{
			token_num = 0;
			memset(line, 0, MAX_LINE);
			continue;		
		}
		difference = total_count - index - 1;
		if (difference < 0)
			difference = 0;
		loop_total = total_count - difference;	
		
		for(int i=0; i < loop_total; i++)
		{
			/*ret = total_count - 1 - index - difference; 
			if(ret != i) 
			{
				cout << "error " << i << " " << ret << " : " << token << " " <<  total_count << " " << strlen(line) << " " << int(token[0]) << endl;
				fprintf (wfptr, "null \t");
				break;
			}*/
			/*if(token[0] == '-')
			{
				fprintf (wfptr, "null \t");
			} else 
				fprintf (wfptr, "%s \t", token);
			*/
			fprintf (wfptr, "%s \t", token);
			index = getToken(line, token);
		}
		for(int i=0; i < difference; i++)
		{
			fprintf (wfptr, "null \t");
		}
		
		token_num = 0;
		fprintf (wfptr, "\n");	
		memset(line, 0, MAX_LINE);
	}

	fclose(rfptr);
	fclose(wfptr);
	
	//string temp = "mv temp.dat ";
	//temp += filename;
	//system(temp.c_str());
	
	return 1;
}
